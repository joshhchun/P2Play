#!/usr/bin/env python3
from Node import Node

class RoutingTable:
    def __init__(self, id):
        self.node_id = id
        self.k = 20
        self.k_buckets = [[] for _ in range(160)]

    def add_node(self, node: Node):
        if node.id == self.node_id:
            return
        bucket_index = self.get_bucket_index(node.id)
        bucket = self.k_buckets[bucket_index]
        if node not in bucket and len(bucket) < 20:
            bucket.append(node)
        # TODO: Handle the case where the bucket is full
    
    
    def remove_node(self, node: Node):
        bucket_index = self.get_bucket_index(node.id)
        bucket = self.k_buckets[bucket_index]
        if node in bucket:
            bucket.remove(node)

    def get_bucket_index(self, node_id: int):
        distance = node_id ^ self.node_id
        return (distance).bit_length() - 1
    
    def __repr__(self):
        result = []
        for buck in self.k_buckets:
            for node in buck:
                result.append(str(node))
        return ', '.join(result)