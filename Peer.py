from __future__  import annotations
from hashlib     import sha1
from Routing     import RoutingTable
from collections import namedtuple
from Node        import Node
from Protocol   import P2PlayProtocol
from KClosestPeers import KClosestPeers

import asyncio
import logging

ALPHA = 3
logger = logging.getLogger(__name__)


class Peer:
    def __init__(self, port: int = 0, bs_host: str = None, bs_port: int = None, bs_id: int = None, _id = None):
        self.node          = Node(_id=_id)
        self.table         = RoutingTable(self.node.id)
        self.k             = 20
        # TODO: Figure out storage 
        self.storage       = {}

    def _create_factory(self):
        '''
        Creates a factory for the node to listen for incoming
        requests.
        Params: None
        Returns: twisted.internet.protocol.Factory
        '''
        return P2PlayProtocol(self)

    async def listen(self, port: int, ip: str = '0.0.0.0'):
        self.node.ip, self.node.port = ip, port
        loop = asyncio.get_event_loop()
        listen = loop.create_datagram_endpoint(self._create_factory, local_addr=(ip, port))
        logger.info(f'Listening on {self.node.ip}:{self.node.port}')
        self.transport, self.protocol = await listen
        # TODO: Refresh Table
        self._schedule_refresh()
    
    def _schedule_refresh(self):
        '''
        Schedules the routing table to be refreshed every hour.
        '''
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh = loop.call_later(3600, self._schedule_refresh)
    
    # TODO: Finish
    async def _refresh_table(self):
        '''
        Refresh the buckets in the routing table that haven't had any lookups in 1 hour.
        '''
        results = []
        for node_id in self.protocol.get_refresh():
            node = Node(_id=node_id)
            nearest = self.table.find_kclosest(node_id, ALPHA)
            # Crawl the network for it...
            # Do not forget to update the buckets last updated time

    
    async def iterative_node_lookup(self, target_id: int) -> list:
        '''
        Finds the closest k nodes to the target_id, iteratively.
        '''
        # Finds ALPHA (3) closest nodes to the target_id, and push to the closest list (acts as starting point)
        neighbors    = self.table.find_kclosest(target_id, ALPHA)
        closest_list = KClosestPeers(self.node)
        closest_list.push_nodes(neighbors)

        # Keep on going until there are no more nodes to contact
        while not closest_list.completed:
            # Get the next ALPHA nodes to send a find_node request to
            nearest_nodes = closest_list.nearest(ALPHA)
            for node in nearest_nodes:
                closest_list.contacted.add(node.id)
                if node.id == target_id:
                    temp_list = self.table.find_kclosest(target_id)
                    continue
                else:
                    # temp_list = self.find_node(node, target_id)
                    temp_list = await self.protocol.make_call(node.id, 'find_node', node.id, (node.ip, node.port), target_id)
                closest_list.push_nodes(temp_list)

        # Return the k closest nodes to the target_id
        return closest_list.result()

    
    async def _bootstrap_node(self, addr: tuple[str, int]):
        '''
        Bootstraps the node to the network.
        Params: host - IP address of the bootstrap node
                port - Port of the bootstrap node
        Returns: Node or None
        '''
        # Send a ping request, which will return the node's ID
        result = await self.protocol.ping(addr)

        # Ping was unsuccessful
        if result[1]:
            return None

        # If the ping was successful, add the node to the routing table
        bootstrap = Node(_id=result[0], ip=addr[0], port=addr[1])
        self.table.add_node(bootstrap)
        return bootstrap
            

    async def bootstrap(self, boostraps: list[tuple[str, int]] = []):
        if not boostraps:
            return
        
        # Try to bootstrap to each node
        tasks = map(self._bootstrap_node(), boostraps)
        results = await asyncio.gather(*tasks)

        # Only keep the nodes that were successfully bootstrapped to
        boostraps = [task for task in results if task]
        print(f"Bootstrapped to {boostraps}")
        
        # self.iterative_node_lookup(self.node.id)
    
    def get_info(self):
        return (self.node.ip, self.node.port, self.node.id)

    def __repr__(self):
        return str(self.node.id)

