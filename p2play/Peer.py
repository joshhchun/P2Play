from __future__           import annotations
from hashlib              import sha1
from collections          import namedtuple
from p2play.Node          import Node
from p2play.Routing       import RoutingTable
from p2play.Protocol      import P2PlayProtocol
from p2play.Crawler       import Crawler

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
        self._schedule_refresh()
    
    def _schedule_refresh(self):
        '''
        Schedules the routing table to be refreshed every hour.
        '''
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh = loop.call_later(3600, self._schedule_refresh)
    
    async def _refresh_table(self):
        '''
        Refresh the buckets in the routing table that haven't had any lookups in 1 hour.
        '''
        for node_id in self.table.refresh_list:
            node_to_find = Node(_id=node_id)
            kclosest     = self.table.find_kclosest(node_id, ALPHA)
            crawler      = Crawler(self.protocol, node_to_find, kclosest, self.k, self.alpha, self.protocol.find_node)

            # Crawl the network for this node, adding the nodes we contact to the routing table
            await crawler.lookup()
    
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
        bootstraps = [task for task in results if task]
        
        network_crawler = Crawler(self.protocol, self.node, bootstraps, self.k, self.alpha, self.protocol.find_node)
        return await network_crawler.lookup()
    
    def get_info(self):
        return (self.node.ip, self.node.port, self.node.id)

    def __repr__(self):
        return str(self.node.id)

