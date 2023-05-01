from p2play.Node import Node
from p2play.Crawler import KClosestNodes


class TestKClosestNodes:
    def test_max_size(self, mknode):
        node = KClosestNodes(mknode(node_id=0), 3, 3)

        for digit in range(10):
            node.push(mknode(node_id=digit))

        assert min(len(node.heap), node.capacity) == 3
        assert len(list(node)) == 3

    def test_iteration(self, mknode):
        heap = KClosestNodes(mknode(node_id=0), 5, 3)
        nodes = [mknode(node_id=x) for x in range(10)]
        for index, node in enumerate(nodes):
            heap.push(node)
        for index, node in enumerate(heap):
            assert index == node.id
            assert index < 5

    def test_remove(self, mknode): 
        heap = KClosestNodes(mknode(node_id=0), 5, 3)
        nodes = [mknode(node_id=x) for x in range(10)]
        for node in nodes:
            heap.push(node)
       
        heap.remove(nodes[0].id)
        heap.remove(nodes[1].id)
        assert len(list(heap)) == 5
        for index, node in enumerate(heap):
            assert index + 2 == node.id
            assert index < 5 