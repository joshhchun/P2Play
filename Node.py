from __future__ import annotations
from random import getrandbits
from hashlib import sha1

class Node:
    def __init__(self, _id: int = None, ip: str = None, port: int = None):
        self.id      = _id or self.generate_id()
        self.ip      = ip
        self.port    = port
    
    # def __iter__(self):
    #     return iter([self.ip, self.port, self.node_id])

    def generate_id(self) -> int:
        rand_num = getrandbits(160)
        return int(sha1(rand_num.to_bytes(160)).hexdigest(), 16)
    
    def distance(self, other: Node) -> int:
        return self.id ^ other.id

    def __repr__(self):
        return f'Node({self.id})'