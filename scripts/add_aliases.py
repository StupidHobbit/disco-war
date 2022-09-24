import asyncio

from disco_war.repository.redis import make_redis
from disco_war.configuration import make_redis_based_configuration
from disco_war.repository import types


async def main():
    r = make_redis()
    configuration = make_redis_based_configuration(r)
    aliases = {
        types.Login('Iva'): types.Login('Iva'),
        types.Login('iva'): types.Login('Iva'),
        types.Login('ШмIфIva'): types.Login('Iva'),
        types.Login('dedcannibal'): types.Login('DEDCANNIBAL'),
        types.Login('artes'): types.Login('Artes'),
        types.Login('stupidhobbit'): types.Login('Artes'),
    }

    for alias, player in aliases.items():
        await configuration.players_controller.add_alias(player, alias)


if __name__ == '__main__':
    asyncio.run(main())
