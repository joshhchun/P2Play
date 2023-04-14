from __future__  import annotations
from hashlib     import sha1
from Routing     import RoutingTable
from collections import namedtuple
from Node        import Node

import sys
import socket
import heapq
import select
import pickle
import random

ALPHA = 3

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
        

class Peer:
    def __init__(self, port: int = 0, bs_host: str = None, bs_port: int = None, bs_id: int = None, _id = None):
        self.node          = Node(_id=_id)
        self.socket        = self.create_socket(port)
        self.table = RoutingTable(self.node.id)
        self.retry_count   = 5
        self.retry_delay   = 5
        self.k             = 20
        # TODO: Figure out storage 
        self.storage       = {}
        self.fill_routing(bs_host, bs_port, bs_id)

    def create_socket(self, port) -> socket.socket:
        '''
        Creates a socket for the node to listen for incoming
        requests.
        Params: None
        Returns: socket.socket
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        sock.settimeout(5)
        self.node.ip  = sock.getsockname()[0]
        self.node.port = int(sock.getsockname()[1])
        return sock

    def run(self):
        while True:
            for socket in select.select([self.socket], [], [], 0)[0]:
                message, (ip, port) = socket.recvfrom(1024)
                self.handle_message(message, ip, port)

    def iterative_node_lookup(self, target_id: int) -> list:
        '''
        Finds the closest k nodes to the target_id, iteratively.
        '''
        # Finds ALPHA (3) closest nodes to the target_id, and push to the closest list (acts as starting point)
        neighbors    = self.table.find_kclosest(target_id, ALPHA)
        closest_list = KClosestPeers(self.node)
        closest_list.push_nodes(neighbors)

        # Keep on going until there are no more nodes to contact
        while not closest_list.completed:
            # Get the next ALPHA nodes to send a find_node request to
            nearest_nodes = closest_list.nearest(ALPHA)

            # TODO: Make this concurrent
            for node in nearest_nodes:
                closest_list.contacted.add(node.id)
                if node.id == target_id:
                    temp_list = self.table.find_kclosest(target_id)
                    continue
                else:
                    temp_list = self.find_node(node, target_id)
                closest_list.push_nodes(temp_list)

        # Return the k closest nodes to the target_id
        return closest_list.result()

    
    # def ping(self, dest_node: Node) -> bool:
    #     '''
    #     Pings the dest_node to see if it is alive.
    #     Params: dest_node - tuple of the IP address and port of the node
    #     Returns: Bool
    #     '''
    #     message = {
    #         'type'        : 'PING',
    #         'node_id'     : self.node.id,
    #         'node_address': [self.node.ip, self.node.port],
    #     }
    #     pick_obj = pickle.dumps(message)

    #     try:
    #         self.socket.sendto(pick_obj, (dest_node.ip, dest_node.port))
    #         response = self.socket.recvfrom(1024)
    #     except socket.timeout:
    #         print(f'Ping timeout to {dest_node.id} at {dest_node.ip}:{dest_node.port}')
    #         return False
    #     return True

    def find_node(self, dest_node: Node, target_id: int):
        '''
        Sends a find_node request to the dest_node to find the
        k closest nodes to the to_find_node.
        '''
        # if not self.ping(dest_node):
        #     # Remove node from routing table
        #     self.routing_table.remove_node(dest_node)
        #     return []

        message = {
            'type'        : 'FIND_NODE',
            'node_id'     : self.node.id,
            'node_address': [self.node.ip, self.node.port],
            'target_id'   : target_id,
        }
        pick_obj = pickle.dumps(message)
        self.socket.sendto(pick_obj, (dest_node.ip, dest_node.port))

        try:
            response, _ = self.socket.recvfrom(1024)
            response    = pickle.loads(response)
            kclosest    = response["closest"]
            return kclosest
        except socket.timeout:
            print(f"Find node timeout to {dest_node.id} at {dest_node.ip}:{dest_node.port}")
            return []

    
    def fill_routing(self, bs_host: str, bs_port: int, bs_id: int):
        # You are first node in network
        if not bs_host or not bs_port or not bs_id:
            return

        # Boostrap node	
        bs_node = Node(bs_id, bs_host, bs_port)
        self.table.add_node(bs_node)

        # Find k closest nodes to self
        for node in self.iterative_node_lookup(self.node.id):
            self.table.add_node(node)
    
    def get_info(self):
        return (self.node.ip, self.node.port, self.node.id)

    # ------------------ RPC Methods ------------------ #

    def handle_message(self, message, ip, port):
        message = pickle.loads(message)
        if   message["type"] == "PING":
            self.handle_ping(message, ip, port)
        elif message["type"] == "FIND_NODE":
            self.handle_find_node(message, ip, port)
        elif message["type"] == "FIND_VALUE":
            self.handle_find_value(message, ip, port)

    def handle_find_value(self, message: dict, ip: str, port: int):
        ...

    def handle_ping(self, message, ip, port):
        response = {
            'type'        : 'PONG',
            'node_id'     : self.node.id,
            'node_address': [self.node.ip, self.node.port],
        }
        self.socket.sendto(pickle.dumps(response), (ip, port))
    
    def handle_find_node(self, message, ip, port):
        target_id   = int(message["target_id"])
        source_node = Node(int(message["node_id"]), ip, port)
        self.table.add_node(source_node)

        kclosest = self.table.find_kclosest(target_id)
        response = {
            'type'        : 'FIND_NODE_RESPONSE',
            'node_id'     : self.node.id,
            'node_address': [self.node.ip, self.node.port],
            'closest'     : kclosest,
        }

        print("Sending response...")
        self.socket.sendto(pickle.dumps(response), (ip, port))
        print(f"In node {self.node.id}, sent response {response} to {ip}:{port}")

    def __repr__(self):
        return str(self.node.id)

def main():
    if len(sys.argv) > 3:
        bs_host = sys.argv[1]
        bs_port = int(sys.argv[2])
        bs_id   = int(sys.argv[3])
        my_node = Node(bs_host, bs_port, bs_id)
    else:
        my_node = Node()
    my_node.run()

if __name__ == "__main__":
    main()
