import asyncio

from disco_war.repository.redis import make_redis
from disco_war.configuration import make_redis_based_configuration
from disco_war.repository import types


async def main():
    r = make_redis()
    configuration = make_redis_based_configuration(r)
    results = {
        types.Login('Iva'): 4,
        types.Login('DEDCANNIBAL'): 3,
        types.Login('ckipen'): 4,
        types.Login('Artes'): 6,
    }

    games_played = sum(results.values())
    async with configuration.context_manager.start() as c:
        for player, games_won in results.items():
            for _ in range(games_won):
                await configuration.individual_stats_repository.add_game_won_for_player(
                    c,
                    types.ChangeIndividualStatsOptions(player)
                )
            for _ in range(games_played):
                await configuration.individual_stats_repository.add_game_played_for_player(
                    c,
                    types.ChangeIndividualStatsOptions(player)
                )


if __name__ == '__main__':
    asyncio.run(main())
