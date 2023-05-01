import random
import hashlib
# pylint: disable=no-name-in-module
from struct import pack

import pytest

from p2play.Peer import Peer
from p2play.Node import Node
from p2play.Routing import RoutingTable


@pytest.fixture()
def bootstrap_node(event_loop):
    server = Peer()
    event_loop.run_until_complete(server.listen(8468))

    try:
        yield ('127.0.0.1', 8468)
    finally:
        server.stop()


# pylint: disable=redefined-outer-name
@pytest.fixture()
def mknode():
    def _mknode(node_id=None, ip_addy=None, port=None, intid=None):
        """
        Make a node.  Created a random id if not specified.
        """
        return Node(node_id, ip_addy, port)
    return _mknode


# pylint: disable=too-few-public-methods
class FakeProtocol:  # pylint: disable=too-few-public-methods
    def __init__(self, source_id, ksize=20):
        self.router = RoutingTable(source_id, ksize, self)
        self.storage = {}
        self.id = source_id


# pylint: disable=too-few-public-methods
class FakeServer:
    def __init__(self, node_id):
        self.id = node_id  # pylint: disable=invalid-name
        self.protocol = FakeProtocol(self.id)
        self.router = self.protocol.router


@pytest.fixture
def fake_server(mknode):
    return FakeServer(mknode().id)