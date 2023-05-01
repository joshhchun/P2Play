import asyncio

import pytest

from p2play.Peer import Peer
from p2play.Protocol import P2PlayProtocol


@pytest.mark.asyncio
async def test_storing(bootstrap_node):
    server = Peer()
    await server.listen(bootstrap_node[1] + 1)
    await server.bootstrap([bootstrap_node])
    await server.set('key', 'value')
    result = await server.get('key')

    assert result == 'value'

    server.stop()


class TestSwappableProtocol:
    def test_default_protocol(self):  # pylint: disable=no-self-use
        """
        An ordinary Server object will initially not have a protocol, but will
        have a KademliaProtocol object as its protocol after its listen()
        method is called.
        """
        loop = asyncio.get_event_loop()
        server = Peer()
        assert server.protocol is None
        loop.run_until_complete(server.listen(8469))
        assert isinstance(server.protocol, P2PlayProtocol)
        server.stop()
