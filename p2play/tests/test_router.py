from p2play.Node import Node
from p2play.Bucket import Bucket
from p2play.ClosestNodesTraverser import ClosestNodesTraverser
from p2play.Routing import RoutingTable
import pytest
from random import shuffle

class TestBucket:
    def test_split(self, mknode):
        bucket = Bucket((0, 10), 5)
        bucket.add_node(mknode(node_id=1))
        bucket.add_node(mknode(node_id=5))
        bucket.add_node(mknode(node_id=6))
        one, two = bucket.split()
        assert len(one.nodes) == 2
        assert one.range == (0, 5)
        assert len(two.nodes) == 1
        assert two.range == (6, 10)

    def test_split_no_overlap(self):
        left, right = Bucket((0, 2 ** 160), 20).split()
        assert (right.range[0] - left.range[1]) == 1 
    
    def test_add_node_when_full(self, mknode):
        bucket = Bucket((0, 10), 2)
        assert bucket.add_node(mknode())
        assert bucket.add_node(mknode())
        assert not bucket.add_node(mknode())
        assert len(bucket.nodes) == 2
        assert len(bucket.replacement_cache) == 1
    
    def test_order_of_add_node(self, mknode):
        bucket = Bucket((0, 10), 3)
        nodes = [mknode(), mknode(), mknode()]
        for node in nodes:
            bucket.add_node(node)
        for i, node in enumerate(nodes):
            assert node == nodes[i]
    
    def test_add_same_node_twice(self, mknode):
        bucket = Bucket((0, 10), 2)
        node1 = mknode()
        node2 = mknode()

        bucket.add_node(node1)
        bucket.add_node(node2)
        bucket.add_node(node1)
        assert len(bucket.nodes) == 2
        assert len(bucket.replacement_cache) == 0
        
        all_nodes = bucket.curr_nodes
        assert node1 == all_nodes[1]
    def test_remove_node(self, mknode):
        k = 3
        bucket = Bucket((0, 10), k)
        nodes = [mknode() for _ in range(10)]
        for node in nodes:
            bucket.add_node(node)

        replacement_nodes = bucket.replacement_cache
        assert list(bucket.nodes.values()) == nodes[:k]
        assert list(replacement_nodes.values()) == nodes[k:]

        bucket.remove_node(nodes.pop())
        assert list(bucket.nodes.values()) == nodes[:k]
        assert list(replacement_nodes.values()) == nodes[k:]

        bucket.remove_node(nodes.pop(0))
        assert list(bucket.nodes.values()) == nodes[:k-1] + nodes[-1:]
        assert list(replacement_nodes.values()) == nodes[k-1:-1]

        shuffle(nodes)
        for node in nodes:
            bucket.remove_node(node)

        assert len(bucket.nodes) == 0
        assert len(replacement_nodes) == 0


class TestRoutingTable:
    def test_add_contact(self, fake_server, mknode):
        fake_server.router.add_node(mknode())
        assert len(fake_server.router.buckets) == 1
        assert len(fake_server.router.buckets[0].nodes) == 1

        
@pytest.fixture()
def mknode():
    def _mknode(node_id=None, ip_addy=None, port=None, intid=None):
        return Node(_id=node_id, ip=ip_addy, port=port)
    return _mknode


class FakeProtocol:
    def __init__(self, source_id, ksize=20):
        self.router = RoutingTable(self, ksize, Node(source_id))
        self.storage = {}
        self.source_id = source_id


class FakeServer:
    def __init__(self, node_id):
        self.id = node_id 
        self.protocol = FakeProtocol(self.id)
        self.router = self.protocol.router


@pytest.fixture
def fake_server(mknode):
    return FakeServer(mknode().id)