import asyncio

import w3g

from disco_war.parsing import ReplayFileProcessing, ReplayProcessingResult, UnknownReplay


async def  main():
    f = open(r'C:\Users\User\Documents\Warcraft III\Replay\sc4.w3g', 'rb')

    p = ReplayFileProcessing()
    result = await p.process(f)
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
