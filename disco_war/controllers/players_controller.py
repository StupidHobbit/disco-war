import re
from dataclasses import dataclass

from disco_war.parsing import ReplayProcessingResult
from disco_war.common_types import Login
from disco_war.repository.types import (
    ChangeIndividualStatsOptions,
    RepositoryContextManager,
    PlayersRepository,
    AddPlayerAliasOptions,
    IndividualStatsRepository,
    OneIndividualStatsOptions,
)


@dataclass
class PlayersController:
    context_manager: RepositoryContextManager
    players_repository: PlayersRepository
    individual_stats_repository: IndividualStatsRepository

    async def add_alias(self, player: Login, alias: Login):
        async with self.context_manager.start() as c:
            alias_stats = await self.individual_stats_repository.stats_for_player(c, OneIndividualStatsOptions(alias))
            if alias_stats is not None:
                await self.individual_stats_repository.add_game_played_for_player(
                    c,
                    ChangeIndividualStatsOptions(player=player, amount=alias_stats.games_played),
                )
                await self.individual_stats_repository.add_game_won_for_player(
                    c,
                    ChangeIndividualStatsOptions(player=player, amount=alias_stats.games_won),
                )
                await self.individual_stats_repository.remove_stats(c, OneIndividualStatsOptions(alias))
            await self.players_repository.add_alias(c, AddPlayerAliasOptions(alias=alias, login=player))

    async def normalize_logins(self, result: ReplayProcessingResult) -> ReplayProcessingResult:
        logins = [p.login for p in result.players] + [result.winner]
        logins = [cleanup_login_re.sub('', login) for login in logins]
        async with self.context_manager.start() as c:
            login_to_normalized_login = dict(zip(
                logins,
                await self.players_repository.normalize_players(c, logins),
            ))
        for p in result.players:
            p.login = patch_login(p.login, login_to_normalized_login)
        if result.winner is not None:
            result.winner = patch_login(result.winner, login_to_normalized_login)
        return result


def patch_login(login: Login, login_to_normalized_login: dict[Login, Login]) -> Login:
    return Login(cleanup_login_re.sub('', login_to_normalized_login.get(login) or login))


cleanup_login_re = re.compile(r'#\d+$')
