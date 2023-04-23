#!/usr/bin/env python3

import argparse
import asyncio

from functools import partial
from concurrent.futures.thread import ThreadPoolExecutor
import logging

import sys
from Peer import Peer

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


async def shell(peer):
    '''
    Asynchronously keep reading commands from command line
    '''
    get_input = partial(asyncio.get_event_loop().run_in_executor, ThreadPoolExecutor(1))

    while True:
        line = await get_input(input, ">>> ")
        message = line.rstrip().split(' ')

        if message[0] == "put":
            song_name, artist_name = message[1], message[2]
            print(f"Putting {song_name} by {artist_name}")
            await peer.put(song_name, artist_name)
        if message[0] == "get":
            song_name, artist_name = message[1], message[2]
            print(f"Getting {song_name} by {artist_name}")
            kad_file = await peer.get(song_name, artist_name)
            if kad_file:
                print(f"Succesfully retrieved {song_name} by {artist_name}: storing {kad_file.version}") 
            else:
                print(f"Could not find {song_name} by {artist_name}")
        if message[0] == "storage":
            print(peer.storage)
        if message[0] == "table":
            print(peer.table)
        if message[0] == "find":
            find_node = int(message[1])
            result, nodes = await peer.find_contact(find_node, peer.k)
            if result:
                print(f"Found {find_node} with closest: {nodes}")
            else:
                print(f"Could not find {find_node} with closest: {nodes}")
        if message[0] == "info":
            print(peer.get_info())
        sys.stdout.flush()


def main():
    peer = Peer(k=8)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(peer.listen(10_000))
    loop.run_until_complete(peer.bootstrap([('127.0.0.1', 9000)]))

    loop.run_until_complete(shell(peer))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        peer.stop()
        loop.close()


if __name__ == "__main__":
    main()

