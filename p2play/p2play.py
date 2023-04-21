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
    parser.add_argument("-i", "--ip", help="IP address of existing node", type=str, default=None)
    parser.add_argument("-p", "--port", help="port number of existing node", type=int, default=None)
    parser.add_argument("-id", "--id", help="id of existing node", type=int, default=None)
    parser.add_argument("-mp", "--myport", help="port number of this node", type=int, default=None)

    return parser.parse_args()

async def shell(peer):
    '''
    Asynchronously keep reading commands from command line
    '''
    get_input = partial(asyncio.get_event_loop().run_in_executor, ThreadPoolExecutor(1))

    while True:
        message = await get_input(input, ">>> ")

        if message.startswith("put"):
            line = message.rstrip().split(' ')
            song_name, artist_name = line[1], line[2]
            print(f"Putting {song_name} by {artist_name}")
            await peer.put(song_name, artist_name)
        if message.startswith("get"):
            line = message.rstrip().split(' ')
            song_name, artist_name = line[1], line[2]
            print(f"Getting {song_name} by {artist_name}")
            kad_file = await peer.get(song_name, artist_name)
            if kad_file:
                print(f"Succesfully retrieved {song_name} by {artist_name}: storing {kad_file.version}") 
            else:
                print(f"Could not find {song_name} by {artist_name}")
        if message.startswith("storage"):
            print("Storage: ")
            pprint.pprint(peer.storage)
        if message.startswith("table"):
            print(peer.table)
        # Flush stdout
        sys.stdout.flush()


def connect_node(args, peer):
    port = args.myport
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(peer.listen(port))
    if args.ip and args.port:
        bootstrap_node = (args.ip, int(args.port))
        loop.run_until_complete(peer.bootstrap([bootstrap_node]))
    
    task = shell(peer)
    asyncio.ensure_future(task)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        peer.stop()
        loop.close()



def main():
    args = parse_arguments()
    peer = Peer(args.id)
    connect_node(args, peer)


if __name__ == "__main__":
    main()
    
