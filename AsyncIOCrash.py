import asyncio


async def sleep_and_print(seconds: int) -> None:
  asyncio.sleep(seconds)
  print("Hello, world!")


def call_synchronously() -> None:
  task = sleep_and_print(2)
  asyncio.ensure_future(task)
  print("AYA")
  # ensure_future will run this task in the background; it will run when you
  # `await` a function and "has time to process it"

"""
# This is inside of a non-async function

async def ping_oldest_contact() -> None:
    oldest_contact = bucket.oldest_contact
    try:
        await self.protocol.ping(oldest_contact)
        bucket.add_contact(oldest_contact)
    except Exception as error:
        print("Contact '%s' failed to respond." % oldest_contact)
        bucket.remove_contact(oldest_contact)
        bucket.add_contact(contact)

if not second_attempt:
    if self.can_split(bucket):
        self.split_bucket_index(index)
        self.add_contact(contact, True)
    else:
        task = ping_oldest_contact()
        asyncio.ensure_future(task)
"""

"""

async def listen(self, **kwargs) -> tuple:
    host = kwargs.get("host", self.DEFAULT_HOST)
    port = kwargs.get("port", self.DEFAULT_PORT)

    # Create the function that will create the transport and protocol.
    loop = asyncio.get_event_loop()
    datagramListen = loop.create_datagram_endpoint(
        self.factory,
        local_addr=(host, port),
    )

    # Call the function and get the host and port we are listening on.
    self.transport, self.protocol = await datagramListen
    host, port = self.transport.get_extra_info("sockname")

    self.__scheduleRefresh()

    logger.info("Listening on %s:%d", host, port)
    return host, port
"""

"""
# loop = asyncio.get_event_loop()
# task = None
# loop.run_until_complete(task)
asyncio.ensure_future(task1)
asyncio.ensure_future(task2)
loop.run_forever()

# main

client = ParakeetClient()
task = client.listen()
loop = asyncio.get_event_loop()
loop.run_until_complete(task)

bootstraps = []
for i in range(1, len(sys.argv) - 1, 2):
    host = sys.argv[i]
    port = int(sys.argv[i + 1])
    address = (host, port)
    bootstraps.append(address)

if bootstraps:
    task = client.bootstrap(bootstraps)
    loop.run_until_complete(task)

self.factory = self.__createFactory()

def __createFactory(self) -> ParakeetProtocol:
  return lambda: ParakeetProtocol(self)
"""

"""

class ParakeetProtocol(asyncio.DatagramProtocol):
    REQUEST_TIMEOUT = 2.0

    def __init__(self, client) -> None:
        self.client      = client
        self.transport   = None
        self.outstanding = {}

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data, address) -> None:
        text = data.decode("utf-8").strip()

        # Don't do anything if someone just sent whitespace.
        if text:

            try:
                # Turn the text into a dictionary.
                object = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON: %s", text)
                return

            if "method" in object:
                task = self.handle_request(object, address)
                return asyncio.ensure_future(task)

            if "result" in object:
                return self.handle_response(object)

    async def handle_request(self, object, address) -> None:
        response = None
        function = getattr(self, "remote_" + object["method"])
        object["args"].insert(0, address)

        try:
            result = await function(*object["args"], **object["kwargs"])
            response = self.create_response(object["id"], result, None)
        except Exception as error:
            response = self.create_response(object["id"], None, error)

        text = json.dumps(response)
        data = text.encode("utf-8")
        self.transport.sendto(data, address)

    def parse_error(self, object) -> Exception:
        try:
            type = eval(object["type"])
            if issubclass(type, Exception):
                return type(*object["args"])
        finally:
            # We could not figure out the type of the error.
            return Exception(object["type"], *object["args"])

    def handle_response(self, object) -> None:
        future, timer = self.outstanding.pop(object["id"])
        timer.cancel()

        if object["error"] is not None:
            error = self.parse_error(object["error"])
            return future.set_exception(error)

        future.set_result(object["result"])

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
    # Other people call these functions
    
    async def remote_ping(self, address, id) -> str:
        contact = Contact(id, *address, self)
        self.client.table.add_contact(contact)
        return self.client.id

    async def remote_find_node(self, address, id, target) -> list:
        contact = Contact(id, *address, self)
        self.client.table.add_contact(contact)

        # Find the closest nodes to the target.
        contacts = self.client.table.find_closest(target, exclude=id)
        return [
            (contact.id, *contact.address)
            for contact in contacts
        ]


    async def remote_find_value(self, address, id, keyHash, pubkeyHex) -> dict:
        contact = Contact(id, *address, self)
        self.client.table.add_contact(contact)

        result = {}
        try:
            # Fetch ``(value, deleted, version)`` from storage.
            key = (pubkeyHex, keyHash)
            result["value"] = self.client.storage.lookup(key)
        except KeyError:
            pass

        # Find the closest nodes to the target.
        contacts = self.client.table.find_closest(keyHash, exclude=id)
        result["contacts"] = [(x.id, *x.address) for x in contacts]

        return result

    async def call_or_remove(self, id, address, method, *args, **kwargs) -> Any:
        try:
            return await self.call(address, method, *args, **kwargs)
        except asyncio.TimeoutError as error:
            # logger.warning("Peer timed out: %d", id)
            # print("Wait a second,", id, "is dead!")
            self.client.table.remove_contact(id)
            raise error

"""

if __name__ == "__main__":
  task = sleep_and_print(2)
  asyncio.run(task)
