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

    def test_in_range(self, mknode): 
        bucket = Bucket((0, 10), 10)
        assert bucket.in_range(mknode(node_id=5).id) is True
        assert bucket.in_range(mknode(node_id=11).id) is False
        assert bucket.in_range(mknode(node_id=10).id) is False
        assert bucket.in_range(mknode(node_id=0).id) is True

class TestRoutingTable:
    def test_add_contact(self, fake_server, mknode):
        fake_server.router.add_node(mknode())
        assert len(fake_server.router.k_buckets) == 1
        assert len(fake_server.router.k_buckets[0].nodes) == 1

class TestTableTraverser:
    def test_iteration(self, fake_server, mknode):
        """
        Make 10 nodes, 5 buckets, two nodes add to one bucket in order,
        All buckets: [node0, node1], [node2, node3], [node4, node5],
                     [node6, node7], [node8, node9]
        Test traver result starting from node4.
        """

        nodes = [mknode(intid=x) for x in range(10)]

        buckets = []
        for i in range(5):
            bucket = Bucket((2 * i, 2 * i + 1), 2)
            bucket.add_node(nodes[2 * i])
            bucket.add_node(nodes[2 * i + 1])
            buckets.append(bucket)

        # replace router's bucket with our test buckets
        fake_server.router.buckets = buckets

        # expected nodes order
        expected_nodes = [nodes[5], nodes[4], nodes[3], nodes[2], nodes[7],
                          nodes[6], nodes[1], nodes[0], nodes[9], nodes[8]]

        start_node = nodes[4]
        index = fake_server.router.get_bucket_index(start_node.id)
        table_traverser = ClosestNodesTraverser(fake_server.router.k_buckets, index)
        for index, node in enumerate(table_traverser):
            assert node == expected_nodes[index]
        