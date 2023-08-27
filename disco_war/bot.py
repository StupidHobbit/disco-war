import re
from io import BytesIO

import discord
from discord.ext import commands

from disco_war.common_types import Login, GroupDescriptor
from disco_war.controllers.results_processing import ResultAlreadyProcessed, WinnerNotInPlayersException
from disco_war.markdown import MarkdownBuilder
from disco_war.parsing import ReplayFileProcessing, ReplayProcessingResult, UnknownReplay
from disco_war.repository.redis import make_redis
from disco_war.repository import types
from disco_war.configuration import make_redis_based_configuration


class SurvivalChaosClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix='/', intents=intents)

        r = make_redis()
        self.r = r
        self.configuration = make_redis_based_configuration(r)

        @self.command()
        async def stats(ctx: commands.Context):
            await ctx.send(await self.make_stats_message())

        @self.command()
        async def add_alias(ctx: commands.Context, alias: str, player: str):
            await self.configuration.players_controller.add_alias(Login(alias), Login(player))

    async def setup_hook(self):
        await self.r.ping()

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        processing = AttachmentProcessing()
        winner_search = winner_re.search(message.content)
        if winner_search is None:
            winner = None
        else:
            winner = Login(winner_search.group(1))
        for attachment in message.attachments:
            try:
                result = await processing.process(attachment)
            except UnknownReplay as e:
                await message.channel.send(f'Этот реплей карты {e.map_name} не похож на Survival Chaos')
                continue
            if result is None:
                return

            if winner is not None:
                result.winner = winner

            result = await self.configuration.players_controller.normalize_logins(result)

            try:
                await self.configuration.replay_processing.process(result)
            except ResultAlreadyProcessed:
                await message.channel.send(f'Этот реплей (номер {result.id}) уже был обработан')
                continue
            except WinnerNotInPlayersException:
                await message.channel.send(f'Логин победителя ({result.winner}) не найден в реплее карты или алиасах')
                continue

            await message.channel.send(result.formatted())
            stats = await self.make_group_stats_message(GroupDescriptor(frozenset(p.login for p in result.players)))
            await message.channel.send(stats)
        await self.process_commands(message)

    async def make_stats_message(self) -> str:
        stats = await self.configuration.individual_stats_controller.get()
        return f'Статистика по всем игрокам:\n{self.format_stats_message(stats)}'

    async def make_group_stats_message(self, group: GroupDescriptor) -> str:
        stats = await self.configuration.individual_stats_controller.get_group(group)
        return f'Статистика по группе:\n{self.format_stats_message(stats)}'

    def format_stats_message(self, stats: list[types.IndividualStats]) -> str:
        return (MarkdownBuilder(new_line_size=1)
                .text('```')
                .table()
                .with_header(('Игрок', 'Побед', 'Игр сыграно'))
                .with_rows([(p.login, f'{p.games_won}', f'{p.games_played}') for p in stats])
                .text('```')
                .build())


class AttachmentProcessing:
    def __init__(self):
        self.file_processing = ReplayFileProcessing()

    async def process(self, attachment: discord.Attachment) -> ReplayProcessingResult | None:
        if '.w3g' not in attachment.filename:
            return None
        file = BytesIO(await attachment.read())
        return await self.file_processing.process(file)


winner_re = re.compile(r'\+[\d ]*(\w+)')
