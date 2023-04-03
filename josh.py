import hashlib

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.routing_table = RoutingTable()
        self.data_store = {}

class RoutingTable:
    def __init__(self):
        self.k_buckets = [[] for _ in range(NUM_NODES_PER_BUCKET)]

    def add_node(self, node):
        bucket_index = self.get_bucket_index(node.node_id)
        bucket = self.k_buckets[bucket_index]
        if node not in bucket:
            if len(bucket) < 20:
                bucket.append(node)
            else:
                # TODO: handle replacement of nodes in the bucket
                pass

    def get_bucket_index(self, node_id):
        distance = int(node_id, 16) ^ int(self.node_id, 16)
        return (distance).bit_length() - 1
