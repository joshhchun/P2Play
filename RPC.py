#!/usr/bin/env python3
from Routing import RoutingTable

class RpcClient:
    def __init__(self, socket, method, params):
        self.socket = socket
        self.routing_table = RoutingTable(self.node_id)
        self.data_store    = {}
        self.retry_count   = 5
        self.retry_delay   = 5

    def call(self):
        self.socket.send(self.method, self.params)
        return self.socket.recv()