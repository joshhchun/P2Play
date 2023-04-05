from __future__ import annotations
from hashlib import sha1
from Routing import RoutingTable
from collections import namedtuple
from Node import Node
from random import getrandbits
import sys
import socket
import time
import heapq
import select
import pickle


ALPHA = 3


class KClosestPeers:
	def __init__(self, node: Node):
		self.node      = node
		self.k         = 20
		self.heap      = []
		self.contacted = set()
	
	@property
	def unseen(self):
		return [node.id for node in self.heap if node.id not in self.seen]
	
	@property
	def completed(self):
		return len(self.contacted) == len(self.heap)
	
	def push(self, distance: int, node_id: int, ip: str, port: int):
		if node_id in self.seen:
			return
		heapq.heappush(self.heap, (distance, node_id, ip, port))
	
	def push_nodes(self, nodes):
		if type(nodes) != list:
			nodes = [nodes]
		for node in nodes:
			# Found the node
			if node.id == self.node.id:
				return 
			distance = self.node.distance(node)
			heapq.heappush(self.heap, (distance, node))
	
	def nearest(self, limit: int = ALPHA):
		'''
		Return the next ALPHA nodes to contact.
		'''
		result = []
		while len(result) < limit and len(self.heap) > 0:
			node = heapq.heappop(self.heap)[1]
			if node.id not in self.contacted:
				result.append(node)
		return result

	def result(self):
		'''
		Return the k closest nodes.
		'''
		return [p[1] for p in heapq.nsmallest(self.k, self.heap)]
		

class Peer:
	def __init__(self, port: int = 0, bs_host: str = None, bs_port: int = None, bs_id: int = None, _id = None):
		self.node          = Node(_id=_id)
		self.socket        = self.create_socket(port)
		self.routing_table = RoutingTable(self.node.id)
		self.retry_count   = 5
		self.retry_delay   = 5
		self.fill_routing(bs_host, bs_port, bs_id)

	def create_socket(self, port) -> socket.socket:
		'''
		Creates a socket for the node to listen for incoming
		requests.
		Params: None
		Returns: socket.socket
		'''
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(('', port))
		sock.settimeout(5)
		self.node.ip  = sock.getsockname()[0]
		self.node.port = int(sock.getsockname()[1])
		return sock

	def run(self):
		while True:
			for socket in select.select([self.socket], [], [], 0)[0]:
				message, (ip, port) = socket.recvfrom(1024)
				self.handle_message(message, ip, port)

	def iterative_node_lookup(self, target_id: int) -> list:
		'''
		Finds the closest k nodes to the target_id, iteratively.
		'''

		# Finds ALPHA (3) closest nodes to the target_id, and push to the closest list (acts as starting point)
		neighbors    = self.find_kclosest(target_id, ALPHA)
		print(f"Neighbors: {neighbors}")
		closest_list = KClosestPeers(self.node)
		closest_list.push_nodes(neighbors)

		# Keep on going until there are no more nodes to contact
		while not closest_list.completed:
			# Get the next ALPHA nodes to send a find_node request to
			nearest_nodes = closest_list.nearest(ALPHA)
			# TODO: Make this concurrent
			for node in nearest_nodes:
				temp_list = self.find_node(node, target_id)
				closest_list.contacted.add(node.id)
				closest_list.push_nodes(temp_list)

		# Return the k closest nodes to the target_id
		return closest_list.result(self.k)

	def find_kclosest(self, target_id: int, limit: int = 20) -> list[Node]:
		'''
		Returns the k closest nodes to the target_id.
		Params: target_id - int, limit - int
		Returns: list of Node objects
		'''
		target       = Node(_id=target_id)
		closest_list = []
		for bucket in self.routing_table.k_buckets:
			for node in bucket:
				distance = target.distance(node)
				print(f"Distance: {distance} | Node: {node} | Target: {target}")
				heapq.heappush(closest_list, (distance, node.id, node.ip, node.port))
		
		return [Node(_id, ip, port) for _, _id, ip, port in heapq.nsmallest(limit, closest_list)]
	
	def generate_id(self) -> int:
		rand_num = getrandbits(160)
		return int(sha1(rand_num.to_bytes(160)).hexdigest(), 16)

	
	def ping(self, dest_node: tuple[str, int]) -> bool:
		'''
		Pings the dest_node to see if it is alive.
		Params: dest_node - tuple of the IP address and port of the node
		Returns: Bool
		'''

		# Build the PING message
		# ROUTING ENTRY: IP address, UDP port, Node ID
		message = {
			'type': 'PING',
			'node_id': self.node.id,
			'node_address': [self.node.ip, self.node.port],
		}
		
		pick_obj = pickle.dumps(message)
		for _ in range(self.retry_count):
			try:
				self.socket.sendto(pick_obj, (dest_node.ip, dest_node.port))
				response = self.socket.recvfrom(1024)
				return True
			except socket.timeout:
				time.sleep(self.retry_delay)
		return False

	def find_node(self, dest_node: Node, target_id: int):
		'''
		Sends a find_node request to the dest_node to find the
		k closest nodes to the to_find_node.
		'''
		# Ping node first to see if it is alive
		# if not self.ping(dest_node):
			# Remove node from routing table
			# self.routing_table.remove_node(dest_node)
			# return []
		
		message = {
			'type': 'FIND_NODE',
			'node_id': self.node.id,
			'node_address': [self.node.ip, self.node.port],
			'target_id': target_id,
		}
		pick_obj = pickle.dumps(message)
		# for _ in range(self.retry_count):
			# try:
		self.socket.sendto(pick_obj, (dest_node.ip, dest_node.port))
		response, _ = self.socket.recvfrom(1024)
		response = pickle.loads(response)
		kclosest = response["closest"]
		return kclosest
			# except socket.timeout:
				# time.sleep(self.retry_delay)

	
	def fill_routing(self, bs_host: str, bs_port: int, bs_id: int):
		if not bs_host and not bs_port and not bs_id:
			return
		
		bs_node = Node(bs_id, bs_host, bs_port)
		self.routing_table.add_node(bs_node)
		x = self.find_node(bs_node, self.node.id)
		print(f"Closest nodes to {self.node.id} from {bs_id}: {x}")
		for node in x:
			self.routing_table.add_node(node)
	
	def get_info(self):
		return (self.node.ip, self.node.port, self.node.id)

	# ------------------ RPC Methods ------------------ #
	def handle_message(self, message, ip, port):
		message = pickle.loads(message)
		if message["type"] == "PING":
			self.handle_ping(message, ip, port)
		elif message["type"] == "FIND_NODE":
			self.handle_find_node(message, ip, port)
		elif message["type"] == "FIND_VALUE":
			self.handle_find_value(message, ip, port)

	def handle_find_value(self, message: dict, ip: str, port: int):
		...

	def handle_ping(self, message, ip, port):
		response = {
			'type': 'PONG',
			'node_id': self.node.id,
			'node_address': [self.node.ip, self.node.port],
		}
		response_bytes = str(response).encode()
		self.socket.sendto(response_bytes, (ip, port))
	
	def handle_find_node(self, message, ip, port):
		target_id = int(message["target_id"])
		kclosest = self.find_kclosest(target_id)
		# Add the source node to the routing table
		source_node = Node(int(message["node_id"]), ip, port)
		self.routing_table.add_node(source_node)

		response = {
			'type': 'FIND_NODE_RESPONSE',
			'node_id': self.node.id,
			'node_address': [self.node.ip, self.node.port],
			'closest': kclosest,
		}
		pick_obj = pickle.dumps(response)
		self.socket.sendto(pick_obj, (ip, port))

def main():
	if len(sys.argv) > 3:
		bs_host = sys.argv[1]
		bs_port = int(sys.argv[2])
		bs_id   = int(sys.argv[3])
		my_node = Node(bs_host, bs_port, bs_id)
	else:
		my_node = Node()
	my_node.run()

if __name__ == "__main__":
	main()
