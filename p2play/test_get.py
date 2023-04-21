#!/usr/bin/env python3
import argparse
import logging
import asyncio
import select 
import aioconsole
from functools import partial
from concurrent.futures.thread import ThreadPoolExecutor

import sys
from Peer import Peer
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


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
		# x = await aioconsole.ainput(">>> ")
		message = await get_input(input, ">>> ")
		if message.startswith("put"):
			line = message.rstrip().split(' ')
			song_name = line[1]
			artist_first, artist_last = line[2].split("_")
			print(song_name, (artist_first, artist_last))
			await peer.put(song_name, f"{artist_first}{artist_last}")
		if message.startswith("get"):
			line = message.rstrip().split(' ')
			song_name = line[1]
			artist_first, artist_last = line[2].split("_")
			print(song_name, (artist_first, artist_last))
			await peer.get(song_name, f"{artist_first}{artist_last}")
		if message.startswith("storage"):
			print(peer.storage)
		if message.startswith("table"):
			print(peer.table)
		# Flush stdout
		sys.stdout.flush()


def connect_to_bootstrap_node(args, peer):
	port = args.myport
	loop = asyncio.get_event_loop()
	loop.set_debug(True)

	loop.run_until_complete(peer.listen(port))
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


def create_bootstrap_node(args, peer):
	port = args.myport
	loop = asyncio.get_event_loop()
	loop.set_debug(True)

	loop.run_until_complete(peer.listen(port))
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
	if args.ip and args.port:
		connect_to_bootstrap_node(args, peer)
	else:
		create_bootstrap_node(args, peer)


if __name__ == "__main__":
	main()
	
