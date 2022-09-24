from dataclasses import dataclass
from operator import attrgetter

from disco_war.parsing import ReplayProcessingResult
from disco_war.repository.types import (
    IndividualStatsRepository,
    IndividualStats,
    ChangeIndividualStatsOptions,
    AllIndividualStatsOptions,
    RepositoryContextManager,
    GameOptions,
    GamesRepository,
    GameID,
    AddGameStatus,
)


class ResultAlreadyProcessed(Exception):
    def __init__(self, result_id: GameID):
        self.result_id = result_id

    def __str__(self):
        return f'Result with id = {self.result_id} is already processed!'


@dataclass
class ReplayResultsProcessing:
    context_manager: RepositoryContextManager
    individual_stats_repository: IndividualStatsRepository
    games_repository: GamesRepository

    async def process(self, result: ReplayProcessingResult):
        async with self.context_manager.start() as c:
            add_game_result = await self.games_repository.add_played_game(c, GameOptions(result.id))
            if add_game_result.status == AddGameStatus.DUPLICATE:
                raise ResultAlreadyProcessed(result.id)

            for player in result.players:
                await self.individual_stats_repository.add_game_played_for_player(
                    c,
                    ChangeIndividualStatsOptions(player=player.login),
                )
            if result.winner is None:
                return
            await self.individual_stats_repository.add_game_won_for_player(
                c,
                ChangeIndividualStatsOptions(player=result.winner),
            )


@dataclass
class IndividualStatsController:
    context_manager: RepositoryContextManager
    individual_stats_repository: IndividualStatsRepository

    async def get(self) -> list[IndividualStats]:
        async with self.context_manager.start() as c:
            stats = await self.individual_stats_repository.stats(c, AllIndividualStatsOptions())
        stats.sort(key=games_won_getter, reverse=True)
        return stats


games_won_getter = attrgetter('games_won')
