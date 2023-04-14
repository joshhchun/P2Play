import asyncio
import logging
import json
from   random import getrandbits
from Node import Node

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
            result = await func(addr, **response["args"])
        except Exception as e:
            logger.exception("Error handling RPC request from %s: %s", addr, method)
            response = self.create_response(response["id"], None, e)
        response = self.create_response(response["id"], result, None)

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

    def handle_response(self, response) -> None:
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

        future.set_result(response["result"])
        del self.outstanding[msg_id]

    def create_request(self, method, *args, **kwargs) -> dict:
        return {
            "id": getrandbits(64),
            "method": method,
            "args": list(args),
            "kwargs": kwargs,
        }

    def on_request_timeout(self, id) -> None:
        error = asyncio.TimeoutError("Request %d timed out." % id)
        future, _ = self.outstanding.pop(id)
        future.set_exception(error)

    def call(self, address, method, *args, **kwargs) -> asyncio.Future:
        request = self.create_request(method, *args, **kwargs)
        text = json.dumps(request)
        data = text.encode("utf-8")
        self.transport.sendto(data, address)

        # Schedule a timeout for the request.
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        timer = loop.call_later(
            self.REQUEST_TIMEOUT,
            self.on_request_timeout,
            request["id"],
        )

        # Store the future for later so we can set the result of it. Keep the
        # timer so we can cancel it if a response comes back.
        self.outstanding[request.get("id")] = (future, timer)
        return future

    def create_response(self, id, result, error) -> dict:
        return {
            "id": id,
            "result": result,
            "error": None if not error else {
                "type": type(error).__name__,
                "args": error.args
            }
        }

    # --------------------------------------------------------------------------
    # RPC Functions

    async def rpc_ping(self, address: tuple, id: int) -> str:
        '''
        Ping the node to check if it is alive.
        Params: address (tuple), id (int)
        Returns: id (int)
        '''
        contact = Node(id, *address)
        self.node.table.try_add(contact)
        return self.node.id

    async def rpc_find_node(self, addr: tuple, id: int, target: int) -> list:
        '''
        Find the closest nodes to the given target.
        Params: address (tuple), id (int), target (int)
        Returns: list of (id, ip, port)
        '''
        contact = Node(id, *addr)
        self.node.table.try_add(contact)

        # Find the closest nodes to the target (excluding the sender)
        nodes = self.node.table.find_kclosest(target, exclude=contact)
        return [
            (node.id, node.ip, node.port)
            for node in nodes
        ]

    async def rpc_find_value(self, address, id, key) -> dict:
        contact = Node(id, *address)
        self.client.table.try_add(contact)
        
        file_path = self.client.storage.get(key, None)
        # If the node does not have the file, return the closest nodes.
        if not file_path:
            return await self.rpc_find_node(address, id, key)
        
        return {
            "file_path": file_path,
        }
    
    async def rpc_store(self, address, id, key, file_path) -> None:
        contact = Node(id, *address)
        self.client.table.try_add(contact)

        self.client.storage[key] = file_path

    # TODO: This function?
    # async def call_or_remove(self, id, address, method, *args, **kwargs) -> Any:
    #     try:
    #         return await self.call(address, method, *args, **kwargs)
    #     except asyncio.TimeoutError as error:
    #         # logger.warning("Peer timed out: %d", id)
    #         # print("Wait a second,", id, "is dead!")
    #         self.client.table.remove_contact(id)
    #         raise error
