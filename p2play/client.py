#!/usr/bin/env python3

import asyncio
import logging
import sys

from Peer import Peer

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def create_bootstrap_node(port):
	server = Peer()
	loop = asyncio.get_event_loop()
	loop.run_until_complete(server.listen(port))
	print(server.get_info())
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()

def connect_to_boostrap(port):
	server = Peer()
	loop = asyncio.get_event_loop()
	loop.run_until_complete(server.listen(port))
	bootstrap_addy = (sys.argv[2], int(sys.argv[3]))
	loop.run_until_complete(server.bootstrap([bootstrap_addy]))
	print(server.get_info())
	print(f"Routing table: {server.table}")
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.close()

def main():
	print("Starting server...")
	if len(sys.argv) < 2:
		print("Usage: python3 client.py <port> [boostrap_host] [bootstrap_port]")
		sys.exit(1)
	port = int(sys.argv[1])
	if len(sys.argv) == 4:
		connect_to_boostrap(port)
	else:
		create_bootstrap_node(port)

if __name__ == '__main__':
	main()
