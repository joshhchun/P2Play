from p2play.Peer import Peer
import asyncio


async def main():
    x = Peer()
    await x.listen(9000)





asyncio.run(main())

