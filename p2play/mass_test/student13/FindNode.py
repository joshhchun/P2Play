#!/usr/bin/env python3

import argparse
import asyncio
import sys
sys.path.append("../../")

from functools import partial
from concurrent.futures.thread import ThreadPoolExecutor
import logging
import pathlib
from time import time_ns

import sys
from Peer import Peer
#
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
            s = time_ns()
            kad_file = await peer.get(song_name, artist_name)
            e = time_ns()
            if kad_file:
                print(f"Successfully retrieved {song_name} by {artist_name}: storing {kad_file.version} in {(e-s)/(10**9)}s") 
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
    path = pathlib.Path(__file__).parent.absolute() / 'kad_files'
    peer = Peer(kad_path=path)
    num = int(sys.argv[1])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(peer.listen(10_000, "student13.cse.nd.edu"))
    s = time_ns()
    loop.run_until_complete(peer.bootstrap([('student12.cse.nd.edu', 9177 + num - 2)]))
    e = time_ns()
    print(f"Joined network in {(e-s) / (10**9)}s")

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

