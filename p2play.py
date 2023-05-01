#!/usr/bin/env python3
import argparse
import logging
import asyncio
import pprint

from functools import partial
from concurrent.futures.thread import ThreadPoolExecutor

import sys
from Peer import Peer

# log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.addHandler(logging.StreamHandler())


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Optional arguments
    parser.add_argument("-b",  "--bootstraps", help="bootstrap node",          type=str, default=None)
    parser.add_argument("-id", "--id", help="id of existing node",             type=int, default=None)
    parser.add_argument("-p",  "--port", help="port number of this node",      type=int, default=None)

    return parser.parse_args()

async def shell(peer):
    '''
    Asynchronously keep reading commands from command line
    '''
    get_input = partial(asyncio.get_event_loop().run_in_executor, ThreadPoolExecutor(1))

    while True:
        line = await get_input(input, ">>> ")
        message = line.rstrip().split(' ')

        if message.startswith("put"):
            song_name, artist_name = message[1], message[2]
            print(f"Putting {song_name} by {artist_name}")
            await peer.put(song_name, artist_name)
        if message.startswith("get"):
            song_name, artist_name = message[1], message[2]
            print(f"Getting {song_name} by {artist_name}")
            kad_file = await peer.get(song_name, artist_name)
            if kad_file:
                print(f"Succesfully retrieved {song_name} by {artist_name}: storing {kad_file.version}") 
            else:
                print(f"Could not find {song_name} by {artist_name}")
        if message.startswith("storage"):
            print(peer.storage)
        if message.startswith("table"):
            print(peer.table)
        sys.stdout.flush()


def main():
    args = parse_arguments()
    peer = Peer(args.id)
    port = args.myport

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(peer.listen(port))

    if args.bootstraps:
        bootstraps = [pair.split(':') for pair in args.bootstraps.split(',')]
        bootstraps = [(ip, int(port)) for ip, port in bootstraps ]
        loop.run_until_complete(peer.bootstrap(bootstraps))
    
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
