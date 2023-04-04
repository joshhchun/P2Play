from hashlib import sha1
import random
import socket
import time


class Node:
    def __init__(self, bs_host: str = "", bs_port: int = -1):
        self.node_id = self.generate_id()
        self.routing_table = RoutingTable()
        self.routing_table.fill_routing(bs_host, bs_port)
        self.data_store    = {}
        self.socket        = self.create_socket()
        self.retry_count   = 5
        self.retry_delay   = 5
    
    def create_socket(self) -> socket.socket:
        '''
        Creates a socket for the node to listen for incoming
        requests.
        Params: None
        Returns: socket.socket
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))
        self.host = sock.getsockname()[0]
        self.port = sock.getsockname()[1]
        sock.settimeout(5)
        return sock

    def generate_id(self) -> int:
        rand_num = random.getrandbits(160)
        return int(sha1(rand_num.to_bytes()).hexdigest())

    
    def ping(self, dest_node: tuple[str, int]) -> bool:
        '''
        Pings the dest_node to see if it is alive.
        Params: dest_node - tuple of the IP address and port of the node
        Returns: Bool
        '''

        # Build the PING message
        # ROUTING ENTRY: IP address, UDP port, Node ID
        message = {
            'type': 'PING',
            'node_id': self.node_id,
            'node_address': [self.host, self.port],
        }
        
        # Serialize the message as bytes
        message_bytes = bytes(str(message), encoding='utf-8')
        for _ in range(self.retry_count):
            try:
                self.socket.sendto(message_bytes, dest_node)
                response = self.socket.recvfrom(1024)
                return True
            except socket.timeout:
                time.sleep(self.retry_delay)
        return False

    def find_node(self, dest_node: tuple[str, int], target_id):
        '''
        Sends a find_node request to the dest_node to find the
        k closest nodes to the to_find_node.
        '''
        # Build the FIND_NODE message
        # ROUTING ENTRY: IP address, UDP port, Node ID    
        message = {
            'type': 'FIND_NODE',
            'node_id': self.node_id,
            'node_address': [self.host, self.port],
            'target_id': target_id,
        }
        
        # Serialize the message as bytes
        message_bytes = bytes(str(message), encoding='utf-8')

        for _ in range(self.retry_count):
            try:
                if self.ping(dest_node):
                    self.socket.sendto(message_bytes, dest_node)
                    response = self.socket.recvfrom(1024)
                    break
                else:
                    ...
                    # TODO: Handle the case where the node is not alive
            except socket.timeout:
                time.sleep(self.retry_delay)

        return response["closest"]
    
    def fill_routing(self, bs_host: str, bs_port: int):
        '''
        If the boostrap host and port are provided, then the node will
        send a find_node request to the bootstrap node to get the
        k closest nodes to the node's id. The node will then add
        those nodes to its routing table.
        '''
        if not bs_host and bs_port < 0:
            return
        
        for node in self.find_node((bs_host, bs_port), self.node_id):
            # node = (node_address, node_port, node_id)
            self.routing_table.add_node(node)

class RoutingTable:
    def __init__(self):
        self.k = 20
        self.k_buckets = [[[] for _ in range(self.k)] for _ in range(160)]

    def add_node(self, node):
        node_addy, node_port, node_id = node
        bucket_index = self.get_bucket_index(node_id)
        bucket = self.k_buckets[bucket_index]
        if node not in bucket:
            if len(bucket) < 20:
                bucket.append(node)
            else:
                # TODO: handle replacement of nodes in the bucket
                bucket[-1] = node

    def get_bucket_index(self, node_id):
        distance = int(node_id, 16) ^ int(self.node_id, 16)
        return (distance).bit_length() - 1
    

def main():
    my_node = Node()

if __name__ == "__main__":
    main()
