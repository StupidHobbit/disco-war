import asyncio

from disco_war.repository.redis import make_redis
from disco_war.configuration import make_redis_based_configuration
from disco_war.repository import types


async def main():
    r = make_redis()
    await r.flushdb()


if __name__ == '__main__':
    asyncio.run(main())
