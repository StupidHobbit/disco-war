from dataclasses import dataclass
from operator import attrgetter

from disco_war.parsing import ReplayProcessingResult
from disco_war.repository import types
from disco_war.common_types import GroupDescriptor, Login


class ResultAlreadyProcessed(Exception):
    def __init__(self, result_id: types.GameID):
        self.result_id = result_id

    def __str__(self):
        return f'Result with id = {self.result_id} is already processed!'


class WinnerNotInPlayersException(Exception):
    def __init__(self, player: Login):
        self.player = player

    def __str__(self):
        return f'Player with login = {self.player} not found in the list of players for this map!'


@dataclass
class ReplayResultsProcessing:
    context_manager: types.RepositoryContextManager
    individual_stats_repository: types.IndividualStatsRepository
    games_repository: types.GamesRepository

    async def process(self, result: ReplayProcessingResult):
        if result.winner not in result.group:
            raise WinnerNotInPlayersException(result.winner)

        async with self.context_manager.start() as c:
            add_game_result = await self.games_repository.add_played_game(c, types.GameOptions(result.id))
            if add_game_result.status == types.AddGameStatus.DUPLICATE:
                raise ResultAlreadyProcessed(result.id)

            group = GroupDescriptor(frozenset(p.login for p in result.players))

            for player in result.players:
                await self.individual_stats_repository.add_game_played_for_player(
                    c,
                    types.ChangeIndividualStatsOptions(player=player.login),
                )
                await self.individual_stats_repository.add_game_played_in_group_for_player(
                    c,
                    types.ChangeIndividualGroupStatsOptions(player=player.login, group=group),
                )
            if result.winner is None:
                return
            await self.individual_stats_repository.add_game_won_for_player(
                c,
                types.ChangeIndividualStatsOptions(player=result.winner),
            )
            await self.individual_stats_repository.add_game_won_in_group_for_player(
                c,
                types.ChangeIndividualGroupStatsOptions(player=result.winner, group=group),
            )


@dataclass
class IndividualStatsController:
    context_manager: types.RepositoryContextManager
    individual_stats_repository: types.IndividualStatsRepository

    async def get(self) -> list[types.IndividualStats]:
        async with self.context_manager.start() as c:
            stats = await self.individual_stats_repository.stats(c, types.AllIndividualStatsOptions())
        stats.sort(key=games_won_getter, reverse=True)
        return stats

    async def get_group(self, group: GroupDescriptor) -> list[types.IndividualStats]:
        async with self.context_manager.start() as c:
            stats = await self.individual_stats_repository.group_stats(c, types.GroupIndividualStatsOptions(group))
        stats.sort(key=games_won_getter, reverse=True)
        return stats


games_won_getter = attrgetter('games_won')
