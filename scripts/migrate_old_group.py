import asyncio

from disco_war.repository.redis import make_redis
from disco_war.configuration import make_redis_based_configuration
from disco_war.repository import types
from disco_war.common_types import GroupDescriptor


async def main():
    r = make_redis()
    configuration = make_redis_based_configuration(r)
    results = {
        types.Login('Iva'): 7,
        types.Login('DEDCANNIBAL'): 7,
        types.Login('ckipen'): 9,
        types.Login('Artes'): 12,
    }
    games_played = sum(results.values())
    group = GroupDescriptor(frozenset(results))

    async with configuration.context_manager.start() as c:
        for player, games_won in results.items():
            await configuration.individual_stats_repository.add_game_won_in_group_for_player(
                c,
                types.ChangeIndividualGroupStatsOptions(
                    player,
                    group,
                    amount=games_won,
                ),
            )
            await configuration.individual_stats_repository.add_game_played_in_group_for_player(
                c,
                types.ChangeIndividualGroupStatsOptions(
                    player,
                    group,
                    amount=games_played,
                ),
            )


if __name__ == '__main__':
    asyncio.run(main())
