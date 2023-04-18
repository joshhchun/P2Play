from Node import Node
ALPHA = 3







# ----------------------------------------------
# TODO: Refactor this entire class
# ----------------------------------------------







class KClosestPeers:
    def __init__(self, node: Node):
        self.node      = node
        self.k         = 20
        self.heap      = []
        self.contacted = set()

    @property
    def completed(self):
        return len(self.contacted) == len(self.heap)

    def push(self, distance: int, node: Node):
        if node.id == self.node.id:
            return
        for i, (d, n) in enumerate(self.heap):
            if n.id == node.id:
                break
            if distance < d:
                self.heap.insert(i, (distance, node))
                break
        else:
            if len(self.heap) < self.k:
                self.heap.append((distance, node))

    def push_nodes(self, nodes):
        if type(nodes) != list:
            nodes = [nodes]
        for node in nodes:
            self.push(node.distance(self.node), node)
    
    def nearest(self, limit: int = ALPHA):
        '''
        Return the next ALPHA nodes to contact.
        '''
        if self.completed:
            return []

        result = []
        for _, node in self.heap:
            if node.id not in self.contacted:
                result.append(node)
                if len(result) == limit:
                    break
        return result

    def result(self):
        '''
        Return the k closest nodes.
        '''
        return [p[1] for p in self.heap[:self.k]]