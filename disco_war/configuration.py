from dataclasses import dataclass

import redis.asyncio as redis

from disco_war.repository import types, redis as redis_types
from disco_war.controllers.results_processing import ReplayResultsProcessing, IndividualStatsController
from disco_war.controllers.players_controller import PlayersController


@dataclass
class AppConfiguration:
    context_manager: types.RepositoryContextManager

    individual_stats_repository: types.IndividualStatsRepository
    games_repository: types.GamesRepository

    replay_processing: ReplayResultsProcessing
    individual_stats_controller: IndividualStatsController
    players_controller: PlayersController


def make_redis_based_configuration(r: redis.Redis) -> AppConfiguration:
    context_manager = redis_types.RepositoryContextManager(r)

    main_keys_manager = redis_types.RedisKeysManager('main')
    individual_stats_keys_manager = main_keys_manager.namespace('individual_stats')
    games_keys_manager = main_keys_manager.namespace('games')
    players_keys_manager = main_keys_manager.namespace('players')

    individual_stats_repository = redis_types.RedisIndividualStatsRepository(r, individual_stats_keys_manager)
    games_repository = redis_types.GamesRepository(r, games_keys_manager)
    players_repository = redis_types.PlayersRepository(r, players_keys_manager)

    replay_processing = ReplayResultsProcessing(context_manager, individual_stats_repository, games_repository)
    individual_stats_controller = IndividualStatsController(context_manager, individual_stats_repository)
    players_controller = PlayersController(context_manager, players_repository, individual_stats_repository)

    return AppConfiguration(
        context_manager,
        individual_stats_repository,
        games_repository,
        replay_processing,
        individual_stats_controller,
        players_controller,
    )
