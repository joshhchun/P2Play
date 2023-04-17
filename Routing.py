#!/usr/bin/env python3
from Node import Node
from Bucket import Bucket
import heapq
import asyncio

class RoutingTable:
	def __init__(self, id):
		self.node_id   = id
		self.k         = 20
		self.k_buckets = [Bucket((0, 2**160), self.k)]
	
	def greet() -> None:
		'''
		Try to add node to routing table
  		'''
		...
	
	def add_node(self, node: Node):
		'''
		Adds a node to the routing table.
		Params: Node
		Returns: None
  		'''
		index  = self.get_bucket_index(node.id)
		bucket = self.k_buckets[index]

		# If bucket is not full then simply add the node and return
		if bucket.add_node(node):
			return
		
		# If the bucket is full and if the buckets range includes the node's id, then split the bucket
		# Sec 4.2
		'''
		If we just see if range includes nodes own id, also splits ranges not containing node's id
		up to b-1 levels. If b=2, then half of the ID space not containing the nodes id 
  		'''
		if bucket.in_range(node.id) or bucket.depth % 5:
			self.split_bucket(bucket, node)
			self.add_node(node)
		else:
			# If we cant split bucket then try to ping the oldest node in the bucket and if it doesn't respond then replace it
			# Make sure that if the node doesn't respond to remove it from routing table
			asyncio.ensure_future(self.protocol.ping(bucket.oldest))
	

	def find_kclosest(self, target_id: int, limit: int = 20, exclude=None) -> list[Node]:
		'''
		Returns the k closest nodes to the target_id.
		Params: target_id - int, limit - int
		Returns: list of Node objects
		'''
		target       = Node(_id=target_id)
		closest_list = []
		for bucket in self.routing_table.k_buckets:
			for node in bucket:
				if node.id == target.id or (exclude and node.same_addr(target)):
					continue
				distance = target.distance(node)
				heapq.heappush(closest_list, (distance, node.id, node.ip, node.port))
		
		return [Node(*args) for _, *args in heapq.nsmallest(limit, closest_list)] 

	def add_node(self, node: Node):
		if node.id == self.node_id:
			return
		bucket_index = self.get_bucket_index(node.id)
		bucket = self.k_buckets[bucket_index]
		if self.not_in_bucket(bucket, node) and len(bucket) < 20:
			bucket.append(node)
		# TODO: Handle the case where the bucket is full
	
	def not_in_bucket(self, bucket, node):
		for n in bucket:
			if n.id == node.id:
				return False
		return True
	
	def remove_node(self, node: Node, _id: int = None):
		if _id:
			node = Node(_id=_id)
		bucket_index = self.get_bucket_index(node.id)
		bucket = self.k_buckets[bucket_index]
		if node in bucket:
			bucket.remove(node)

	def get_bucket_index(self, node_id: int):
		distance = node_id ^ self.node_id
		return (distance).bit_length() - 1
	
	def __repr__(self):
		result = []
		for i, buck in enumerate(self.k_buckets):
			if len(buck) == 0:
				continue
			result.append(f'Bucket {i}: {buck}')
		return '\n'.join(result)

	def __len__(self):
		return sum([len(bucket) for bucket in self.k_buckets])
	
	def __contains__(self, node_id: int):
		bucket_index = self.get_bucket_index(node_id)
		bucket = self.k_buckets[bucket_index]
		for node in bucket:
			if node.id == node_id:
				return True
		return False
		