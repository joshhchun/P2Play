from __future__           import annotations
from hashlib              import sha1
from collections          import namedtuple
# from p2play.Node          import Node
# from p2play.Routing       import RoutingTable
# from p2play.Protocol      import P2PlayProtocol
# from p2play.Crawler       import Crawler
from Node          import Node
from Routing       import RoutingTable
from Protocol      import P2PlayProtocol
from Crawler       import Crawler
from KadFile       import KadFile

import asyncio
import logging
import pathlib
import os

ALPHA      = 3
logger     = logging.getLogger(__name__)
PREFIX_LEN = 16
KAD_DIR    = 'kad_files'


class Peer:
    def __init__(self, _id = None):
        self.node          = Node(_id=_id)
        # TODO: Figure out this server port thing
        self.server_addr   = ('0.0.0.0', 10_000)
        self.k             = 20
        self.alpha         = 3   
        self.protocol      = self._create_factory()
        self.table         = RoutingTable(self.node.id, 20, self.protocol)

        # TODO: Figure out storage 
        self.storage       = {}
    
    async def get(self, song_name: str, artist_name: str) -> KadFile:
        '''
        Gets the max version kad-file from the network from a given song ID.
        Params: key (str)
        Returns: kad-files (dict[dict])
        '''

        # Creating the song_id "song_name - artist_name"
        song_id = f"{song_name} - {artist_name}"
        logger.info(f'Getting {song_id} from the network')

        key = sha1(song_id.encode()).hexdigest()

        # Check if we already have the song
        # TODO: Return what?
        if self.storage.get(key):
            return self.storage[key]

        song_node = Node(_id=key)
        if not (closest_nodes := self.table.find_kclosest(song_node.id)):
            logger.warning('Could not find any nodes close to song ID: %s', song_id)
            return None
        
        # Crawl the network to find the kad-files
        crawler = Crawler(self.protocol, song_node, closest_nodes, self.k, self.alpha, self.protocol.find_value)

        # crawler.lookup() should return the kad_file with the highest version
        kad_file = await crawler.lookup()
        
        # Add the node to the kad_file providers and add the kad_file to the storage
        kad_file.add_provider(self)
        self.storage[key] = kad_file
        
        # Create a co-routine to download the file from the kad_file providers and return if it was successful
        if (result := await self._download_file(kad_file)):
            logger.info(f'Successfully downloaded {song_id}')
            # Send STORE calls to the k closest nodes to the song id to let them know we have the file (ensure future but do not wait for them)
            kclosest_nodes = list(crawler.closest)
            for node in kclosest_nodes:
                asyncio.create_task(self.protocol.store(node, key, kad_file.to_dict()))
            return kad_file
        else:
            logger.warning(f'Failed to download {song_id}')
            return None

        
    async def _download_file(self, kad_file: KadFile) -> bool:
        '''
        Downloads the file from the kad_file providers
        Params: kad_file (KadFile)
        Returns: success (bool)
        '''
        request = {"song_id": kad_file.song_id}
        prefix  = f"{len(request).zfill(PREFIX_LEN)}"
        message = f"{prefix + request}".encode("utf-8")
        downloaded_file = False

        for provider in kad_file.providers:
            node_id, addr = provider 
            try:
                future         = asyncio.open_connection(*addr)
                reader, writer = await asyncio.wait_for(future, timeout=5)

                # Send the request to the provider for the file
                writer.write(message)
                await writer.drain()

                # Read the file from the provider
                prefix     = await reader.read(PREFIX_LEN)
                buffer     = bytearray()
                size       = int(prefix)

                while len(buffer) < size:
                    data = await reader.read(size - len(buffer))
                    buffer += data
                break
            except Exception as e:
                logger.warning('Could not connect to provider for downloading %s: %s', node_id, e)
        
        if not downloaded_file:
            logger.warning('Could not download file from any provider')
            return False

        # TODO: Put this somewhere else. Create KAD_DIR if it does not exist
        if not os.path.exists(KAD_DIR):
            os.makedirs(KAD_DIR)
        
        # Save the file to the kad_files directory with the song_id as the file name
        kad_path = pathlib.Path(__file__).parent.absolute() / KAD_DIR
        file_path = pathlib.Path(kad_path, f"{kad_file.song_id}.kad")
        with open(file_path, 'wb') as f:
            f.write(buffer)
        return True

        
    async def put(self, song_name, artist_name) -> bool:
        '''
        Upload a kad-file to the network.
        Params: song_name (str), artist_name (str)
        Returns: success (bool)
        '''
        song_id = f"{song_name} - {artist_name}"
        logger.info(f'Putting {song_id} on the network')
        key = sha1(song_id.encode()).hexdigest()
        song_node = Node(_id=key)

        kad_file = await self._construct_kad_file(song_name, artist_name)
        if not (closest_nodes := self.table.find_kclosest(song_node.id)):
            logger.warning('Could not find any nodes close to song ID: %s', song_id)
            return None
        
        # Crawl network for k closest nodes to song id
        crawler = Crawler(self.protocol, song_node, closest_nodes, self.k, self.alpha, self.protocol.find_node)
        kclosest_nodes = await crawler.lookup()

        # Send a STORE call to each of the k closest nodes
        futures = [self.protocol.store(node, kad_file.dict) for node in kclosest_nodes]
         
        # Return true if any of the STORE calls return true
        return any(await asyncio.gather(*futures))

    
    async def _construct_kad_file(self, song_name: str, artist_name: str) -> KadFile: 
        '''
        Given a song name and artist name, constructs a new kad-file.
        Params: song_name (str), artist_name (str)
        Returns: KadFile
        '''
        # First, try to find the largest version # of the kad file in the network (if exists)
        kad_file = await self.get(song_name, artist_name)
        max_version = 0 if not kad_file else kad_file.version

        # TODO: Store Node ID or Ip and port?
        return KadFile({
            'version': max_version + 1,
            'song_name': song_name,
            'artist_name': artist_name,
            'providers': [self.node]
        })

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
        logger.debug(f'Bootstrapping to {addr}...')
        result = await self.protocol.direct_ping(addr)

        # Ping was unsuccessful
        if result[1]:
            return None

        # If the ping was successful, add the node to the routing table
        bootstrap = Node(_id=result[0], ip=addr[0], port=addr[1])
        self.table.add_node(bootstrap)
        return bootstrap
            

    async def bootstrap(self, bootstraps: list[tuple[str, int]] = []):
        if not bootstraps:
            return
        
        # Try to bootstrap to each node
        tasks = map(self._bootstrap_node, bootstraps)
        results = await asyncio.gather(*tasks)

        # Only keep the nodes that were successfully bootstrapped to
        bootstraps = [task for task in results if task]
        
        network_crawler = Crawler(self.protocol, self.node, bootstraps, self.k, self.alpha, self.protocol.find_node)
        return await network_crawler.lookup()
    
    def get_info(self):
        return (self.node.ip, self.node.port, self.node.id)

    def __repr__(self):
        return str(self.node.id)

