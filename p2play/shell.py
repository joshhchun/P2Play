from Peer import Peer
import asyncio
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


async def main():
    peer = Peer()
    await peer.listen(9000)

    try:
        await asyncio.sleep(3600)
    finally:
        peer.close()


if __name__ == "__main__":
    asyncio.run(main())
