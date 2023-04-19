from Node import Node
from KadFile import KadFile
import asyncio
import heapq

class KClosestNodes:
	def __init__(self, node: Node, capacity: int, alpha: int, nodes: list[Node] = []):
		self.node      = node
		self.heap      = []
		self.contacted = set()
		self.exclude   = set()
		self.capacity  = capacity
		self.alpha     = alpha
		if nodes:
			self.push_nodes(nodes)
	
	def get(self, node_id: int):
		'''
		Get a node from the heap by its id
		'''
		for _, node in self.heap:
			if node.id == node_id:
				return node
		return None

	def push(self, node: Node):
		'''
		Push a single node to the heap
		'''
		if node in self:
			return
		distance = node.distance(self.node), 
		heapq.heappush(self.heap, (distance, node))

	def push_nodes(self, nodes: list[Node]):
		'''
		Push a list of nodes to the heap
		'''
		if type(nodes) != list:
			nodes = [nodes]
		
		for node in nodes:
			if node.id == self.node.id:
				self.mark_contacted(node)
			self.push(node)
	
	def remove(self, node_id: int):
		'''
		Remove a node from the heap
		'''
		self.exclude.add(node_id)
		self.heap = [p for p in self.heap if p[1].id != node_id]
		heapq.heapify(self.heap)
	
	def mark_contacted(self, node: Node):
		'''
		Mark a node as contacted
		'''
		self.contacted.add(node.id)


	def __contains__(self, node: Node):
		if node in self.exclude:
			return True
		if any([peer.id == node.id for _, peer in self.heap]):
			return True
		return False
	
	def nearest(self):
		'''
		Return the next ALPHA nodes to contact.
		'''
		result = []
		for _, node in self.heap:
			if node.id not in self.contacted:
				result.append(node)
				if len(result) == self.alpha:
					break
		return result
	
	@property
	def completed(self):
		'''
		It is completed when closest k nodes have been contacted.
		'''
		nodes = heapq.nsmallest(self.capacity, self.heap)
		nodes = [node for _, node in nodes if node.id not in self.contacted]
		return not len(nodes)
	
	def __iter__(self):
		yield from [node for _, node in heapq.nsmallest(self.capacity, self.heap)]


class Crawler:
	def __init__(self, protocol, target, nodes, k, alpha, method):
		self.protocol = protocol
		self.k        = k
		self.alpha    = alpha
		self.closest  = KClosestNodes(target, k, alpha, nodes)
		self.target   = target
		self.method   = method

	async def lookup(self):
		'''
		Finds the k-closest nodes to the target, iteratively (or returns the value if found)
		'''
		id_future_mapping = {}

		# Get ALPHA # of nodes to contact
		for node in self.closest.nearest():
			# Keep track of the node and its future
			id_future_mapping[node.id] = self.method(node, self.target.id)
			self.closest.mark_contacted(node)
		
		# Wait for the results
		routines = await asyncio.gather(*id_future_mapping.values())
		results = dict(zip(id_future_mapping.keys(), routines))

		if self.method == self.protocol.find_value:
			return await self._handle_value_iter(results)
		return await self._handle_node_iter(results)


	async def _handle_value_iter(self, responses):
		"""
		Handle the responses from the nodes we contacted in the lookup. If we are completed then return the k closest nodes. Otherwise, continue the node_lookup.
		"""
		found_values = []
		for node_id, response in responses.items():
			result, err = response 
			if err:
				self.closest.remove(node_id)
			# Found a value
			elif type(result) == dict:
				found_values.append(result)
			else:
				self.closest.push_nodes(result)
		
		# If we found the value then handle
		if found_values:
			return self._handle_found_values(found_values)
		
		# If we couldn't find the vlaue
		if self.closest.completed:
			return None

		return await self.lookup()
	
	def _handle_found_values(self, found_values) -> KadFile:
		"""
		Handle the kad files we found in the lookup. If there is just one then return it. Otherwise, return the one with the highest version.
		"""
		# If we found the value then return it
		if len(found_values) == 1:
			return found_values[0]
		
		# Pick the document with highest document version
		max_version_doc = found_values[0]
		for kad_file in found_values[1:]:
			if kad_file['version'] > max_version_doc['version']:
				max_version_doc = kad_file
		
		return KadFile(max_version_doc)

	async def _handle_node_iter(self, responses):
		"""
		Handle the responses from the nodes we contacted in the lookup. If we are completed then return the k closest nodes. Otherwise, continue the node_lookup.
		"""
		for node_id, response in responses.items():
			result, err = response 
			if err:
				self.closest.remove(node_id)
			else:
				self.closest.push_nodes(self.convert_to_nodes(result))
		
		if self.closest.completed:
			return list(self.closest)

		return await self.lookup()
	
	def convert_to_nodes(self, nodes: tuple) -> list[Node]:
		'''
		Convert a list of tuples (id, ip, port) into nodes
		'''
		return [Node(*args) for args in nodes] if nodes else []
