from __future__           import annotations
from hashlib              import sha1
# from p2play.Node          import Node
# from p2play.Routing       import RoutingTable
# from p2play.Protocol      import P2PlayProtocol
# from p2play.Crawler       import Crawler
from Node          import Node
from Routing       import RoutingTable
from Protocol      import P2PlayProtocol
from Crawler       import Crawler
from KadFile       import KadFile
from typing import Union
import json

import asyncio
import logging
import pathlib
import os

ALPHA       = 3
logger      = logging.getLogger(__name__)
PREFIX_LEN  = 16

class Peer:
    def __init__(self, _id = None):
        self.node          = Node(_id=_id)
        # TODO: Figure out this server port thing
        self.k             = 20
        self.alpha         = 3   
        self.protocol      = self._create_factory()
        self.table         = RoutingTable(self.node.id, 20, self.protocol)
        self.kad_path      = pathlib.Path(__file__).parent.absolute() / 'kad_files'

        self.storage       = {}
    
    async def get(self, song_name: str, artist_name: str) -> Union[KadFile, None]:
        '''
        Gets the max version kad-file from the network from a given song ID.
        Params: key (str)
        Returns: kad-files (dict[dict])
        '''

        # Creating the song_id "song_name - artist_name"
        song_id = f"{song_name} - {artist_name}"
        logger.info(f'Getting {song_id} from the network')

        key = int(sha1(song_id.encode()).hexdigest(), 16)

        # TODO: Check if we already have the song
        # if self.storage.get(key):
        #     logger.debug(f'Already have {song_id}')
        #     return self.storage[key]

        song_node = Node(_id=key)
        if not (closest_nodes := self.table.find_kclosest(song_node.id)):
            logger.warning('Could not find any nodes close to song ID: %s', song_id)
            return None
        
        logger.debug("Starting to crawl network for kad-file %s with closest_nodes: %s", song_id, closest_nodes)
        # Crawl the network to find the kad-files
        crawler = Crawler(self.protocol, song_node, closest_nodes, self.k, self.alpha, "find_value")

        # crawler.lookup() should return the kad_file with the highest version
        kad_file = await crawler.lookup()
        if not kad_file:
            logger.debug("Could not find kad-file for %s", song_id)
            return None
        
        # Create a co-routine to download the file from the kad_file providers and return if it was successful
        if await self._download_file(kad_file):
            logger.info(f'Successfully downloaded {song_id}')
            logger.debug(f'Successfully downloaded {song_id}')
            kad_file.add_provider(self)
            self.storage[key] = kad_file

            # Send STORE calls to the k closest nodes to the song id to let them know we have the file (ensure future but do not wait for them)
            kclosest_nodes = list(crawler.closest)
            for node in kclosest_nodes:
                asyncio.create_task(self.protocol.store(node, key, kad_file.dict))
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
        downloaded_file = False

        logger.debug("Providers for file: %s", kad_file.providers)
        for provider in kad_file.providers:
            node_id, addr = provider 
            try:
                logger.debug("In _download_file, connecting to %s", addr)
                # Send a `SEND_FILE` RPC request to the provider of the file
                await self.protocol.direct_send_file(tuple(addr), kad_file.song_id)
                logger.debug("Sent the send_file RPC request to the provider")
                buffer = None

                async def _download_file_handler(reader, writer):
                    logger.debug("In _download_file_handler")

                    # Read the file from the provider
                    prefix     = await reader.read(PREFIX_LEN).decode("utf-8")
                    logger.debug("Successfully read the prefix from the provider, prefix: %s", prefix)
                    buffer     = bytearray()
                    size       = int(prefix)

                    # Read exactly size # of bytes
                    buffer = await reader.readexactly(size)
                    buffer = buffer.decode("utf-8")
                    logger.debug("Successfully read the file from the provider, buffer: %s", buffer)
                    writer.close()
                    await writer.wait_closed()
                
                server = await asyncio.start_server(_download_file_handler, host=self.node.ip, port=self.node.port)
                # Run server until complete
                async with server:
                    await server.start_serving()
                
                logger.debug("Successfully connected to the provider")
                downloaded_file = True
                break
            except Exception as e:
                logger.warning('Could not connect to provider for downloading %s: %s', node_id, e)
                raise e
                self.table.remove_node(Node(node_id))
        
        if not downloaded_file:
            logger.warning('Could not download file from any provider')
            return False

        # TODO: Put this somewhere else. Create KAD_DIR if it does not exist
        if not os.path.exists(self.kad_path):
            os.makedirs(self.kad_path)
        
        # Save the file to the kad_files directory with the song_id as the file name
        # TODO: Change the path back to original
        file_path = pathlib.Path(self.kad_path, f"{kad_file.song_id}.kad.new")
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
        key       = int(sha1(song_id.encode()).hexdigest(), 16)
        song_node = Node(_id=key)

        if not (result := await self._construct_kad_file(song_name, artist_name, song_node)):
            return False
        kad_file, closest_nodes = result

        # Send a STORE call to each of the k closest nodes
        futures = [self.protocol.store(node, key, kad_file.dict) for node in closest_nodes]
         
        # Return true if any of the STORE calls return true
        return any(await asyncio.gather(*futures))

    
    async def _construct_kad_file(self, song_name: str, artist_name: str, song_node: Node) -> KadFile: 
        '''
        Given a song name and artist name, constructs a new kad-file.
        Params: song_name (str), artist_name (str)
        Returns: KadFile
        '''
        # Get k closest neighbors
        if not (closest_nodes := self.table.find_kclosest(song_node.id)):
            logger.warning('Could not find any nodes close to song ID: %s', song_node.id)
            return None

        crawler  = Crawler(self.protocol, song_node, closest_nodes, self.k, self.alpha, "find_value")
        # First, try to find the largest version # of the kad file in the network (if exists)
        kad_file = await crawler.lookup()
        max_version = 0 if not kad_file else kad_file.version

        return KadFile({
            'version'    : max_version + 1,
            'song_name'  : song_name,
            'artist_name': artist_name,
            'providers'  : [(self.node.id, (self.node.ip, self.node.port))]
        }), crawler.closest

    async def send_file(self, sender_addr: tuple, sender_id: int, song_id: str) -> int:
        '''
        Sends the file to the requesting node.
        Params: sender_addr (tuple), sender_id (int), song_key (str)
        Returns: success (bool)
        '''
        logger.debug("In send_file, sending file %s to %s", song_id, sender_addr)
        # if not (kad_file := self.storage.get(song_key)):
        #     logger.warning('Could not find file %s in storage', song_key)
        #     return False

        song_path = pathlib.Path(self.kad_path) / f"{song_id}.kad"
        logger.info(f'Sending {song_path} to {sender_id}...')

        try:
            # Read the file from the kad_files directory
            with open(song_path, 'rb') as f:
                buffer = f.read()

            size = len(buffer)
            prefix = f"{size}".zfill(PREFIX_LEN)
            message = f"{prefix}{buffer}".encode("utf-8")

            logger.debug("In send_file, trying to connect to %s", sender_addr)
            _, writer = await asyncio.open_connection(*sender_addr)
            logger.debug("In send_file, successfully connected to %s", sender_addr)
            # future         = asyncio.open_connection(*sender_addr)
            # _, writer = await asyncio.wait_for(future, timeout=10)

            # Send the file to the requesting node
            writer.write(message)
            logger.debug("In send_file, successfully wrote to %s", sender_addr)
            await writer.drain()
            await writer.wait_closed()

            return True
        except Exception as e:
            logger.warning('Could not send file %s to %s: %s', song_path, sender_id, e)
            return False
        

    def _create_factory(self):
        '''
        Creates a factory for the node to listen for incoming
        requests.
        Params: None
        Returns: twisted.internet.protocol.Factory
        '''
        return P2PlayProtocol(self)

    async def listen(self, port: int, ip: str = '127.0.0.1'):
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
            kclosest     = self.table.find_kclosest(node_id, limit=ALPHA)
            crawler      = Crawler(self.protocol, node_to_find, kclosest, self.k, self.alpha, "find_node")

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
        
        network_crawler = Crawler(self.protocol, self.node, bootstraps, self.k, self.alpha, "find_node")
        return await network_crawler.lookup()
    
    def get_info(self):
        return (self.node.ip, self.node.port, self.node.id)

    def __repr__(self):
        return str(self.node.id)

