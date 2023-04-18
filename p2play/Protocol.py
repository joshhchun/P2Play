import asyncio
import logging
import json
from   random import getrandbits
from   Node import Node

logger = logging.getLogger(__name__)

class P2PlayProtocol(asyncio.DatagramProtocol):
    '''
    Protocol implementation for the P2Play protocol using asyncio to handle async IO.
    '''
    REQUEST_TIMEOUT = 2.0

    def __init__(self, client) -> None:
        '''
        Create a new P2PlayProtocol instance.
        '''
        self.client      = client
        self.transport   = None
        self.outstanding = {}

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data, addr) -> None:
        text = data.decode("utf-8").strip()

        try:
            response = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON from %s: %s", addr, text)
            return

        match response["type"]:
            case "request":
                task = self.handle_request(response, addr)
                return asyncio.ensure_future(task)
            case "result":
                return self.handle_response(response)
            case _:
                logger.warning("Received invalid message from %s: %s", addr, text)

    async def handle_request(self, response: dict, addr: str) -> None:
        method   = response["method"]
        func     = getattr(self, "rpc_%s" % method)

        # Make sure the method exists and is callable.
        if func is None or not callable(func):
            logger.warning("Received invalid RPC method from %s: %s", addr, method)
            return

        try:
            result = await func(addr, *response["args"])
            response = self.create_response(response["id"], result, None)
        except Exception as e:
            logger.exception("Error handling RPC request from %s: %s", addr, method)
            response = self.create_response(response["id"], None, e)

        text = json.dumps(response)
        data = text.encode("utf-8")
        self.transport.sendto(data, addr)

    # TODO: Error handling
    # def parse_error(self, response) -> Exception:
    #     try:
    #         type = eval(response["type"])
    #         if issubclass(type, Exception):
    #             return type(*response["args"])
    #     finally:
    #         # We could not figure out the type of the error.
    #         return Exception(response["type"], *response["args"])

    def handle_response(self, response: dict) -> None:
        '''
        Handle a response from a RPC call we made
        Params: response (dict)
        Returns: None
        '''
        msg_id = response["id"]
        if msg_id not in self.outstanding:
            logger.warning("Received response for unknown request: %s", msg_id)
            return

        future, timeout = self.outstanding.pop(msg_id)
        timeout.cancel()

        # TODO: Error handling
        # if response["error"] is not None:
        #     error = self.parse_error(response["error"])
        #     return future.set_exception(error)

        future.set_result((response["result"], None))
        self.client.table.greet()

    def create_request(self, method, *args, **kwargs) -> dict:
        return {
            "type"   : "request",
            "id"     : getrandbits(64),
            "method" : method,
            "args"   : list(args),
            "kwargs" : kwargs,
        }

    def _on_timeout(self, id) -> None:
        logger.error("Request %d timed out.", id)
        self.outstanding[id][0].set_result((None, asyncio.TimeoutError()))
        future, _ = self.outstanding.pop(id)

    def call(self, addr, method, *args, **kwargs) -> asyncio.Future:
        # Construct the RPC JSON message.
        request = self.create_request(method, *args, **kwargs)
        text    = json.dumps(request)
        data    = text.encode("utf-8")
        self.transport.sendto(data, addr)

        # Schedule a timeout for the request.
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        timer = loop.call_later(
            self.REQUEST_TIMEOUT,
            self._on_timeout,
            request["id"],
        )

        # Store the future for later so we can set the result of it. Keep the
        # timer so we can cancel it if a response comes back.
        self.outstanding[request.get("id")] = (future, timer)
        return future

    def create_response(self, id, result, error) -> dict:
        return {
            "type": "result",
            "id": id,
            "result": result,
            "error": None if not error else {
                "type": type(error).__name__,
                "args": error.args
            }
        }

    # --------------------------------------------------------------------------
    # RPC Functions
    # --------------------------------------------------------------------------

    async def rpc_ping(self, address: tuple, sender_id: int) -> int:
        '''
        Ping the node to check if it is alive.
        Params: address (tuple), id (int)
        Returns: id (int)
        '''
        contact = Node(sender_id, *address)
        # self.node.table.greet(contact)
        return self.client.node.id

    async def rpc_find_node(self, addr: tuple, sender_id: int, target: int) -> list:
        '''
        Find the closest nodes to the given target.
        Params: address (tuple), id (int), target (int)
        Returns: list of (id, ip, port)
        '''
        contact = Node(sender_id, *addr)
        self.node.table.greet(contact)

        # Find the closest nodes to the target (excluding the sender)
        nodes = self.node.table.find_kclosest(target, exclude=contact)
        return [
            (node.id, node.ip, node.port)
            for node in nodes
        ]

    async def rpc_find_value(self, address, sender_id, key) -> dict:
        contact = Node(sender_id, *address)
        self.client.table.greet(contact)
        
        # If the node does not have the file, return the closest nodes.
        if not (doc := self.client.storage.get(key, None)):
            return await self.rpc_find_node(address, sender_id, key)
        
        return doc
    
    async def rpc_store(self, address: tuple, sender_id: int, key: int, new_doc: dict) -> None:
        sender = Node(sender_id, *address)
        self.client.table.greet(sender)

        # If there is no song with the given key, then add it
        if not (curr_doc := self.client.storage.get(key, None)):
            self.client.storage[key] = new_doc
            return

        curr_version = curr_doc["version"]
        # If the doc is newer, update it (if there is a tie then compare by ID)
        if new_doc["version"] >= curr_version:
            if new_doc["version"] == curr_version:
                if new_doc["id"] < sender_id:
                    # If the incoming ID is smaller, then we keep the old doc
                    return
            # Otherwise, we update our local storage
            self.client.storage[key] = new_doc

    async def make_call(self, node, method, *args, **kwargs):
        '''
        Make a RPC call to a node and return the result.
        Params: node (Node), method (str), *args, **kwargs
        Returns: result (dict), error (str)
        '''
        logger.debug("Making call to %s", node)
        addr = (node.ip, node.port)
        result = await self.call(addr, method, self.client.node.id, *args, **kwargs)

        # TODO: Error, right now it captures general errors and timeouts in same way
        if result[1]:
            logger.warning("Error calling %s on %s: %s", method, node, result[1])
            self.client.table.remove_node(_id=node.id)
            return result
      
        # If the node is new, greet it
        self.client.table.greet(node)
        return result

    def __getattr__(self, method):
        '''
        Dynamically create a method for each RPC function.
        Params: method (str)
        Returns: function
        
        Example:
        protocol.find_node(node_to_ask, target_node) -> find_node RPC
        '''
        return lambda node, *args, **kwargs: self.make_call(node, method, *args, **kwargs)
