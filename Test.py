#!/usr/bin/env python3
from Peer import Peer
import sys
import threading

def test_node_lookup():
    threads = []
    peers = []
    # Node 1 in thread 1
    peer1 = Peer(_id=1)
    peers.append(peer1)
    host, port, node_id = peer1.get_info()
    # Run the node in a thread
    t1 = threading.Thread(target=peer1.run)
    t1.start()
    threads.append(t1)

    # Put nodes 1-35 in the routing table of node 1 all in different threads
    for i in range(1, 36):
        print(f"Adding node {i} to routing table of node 1")
        new_peer = Peer(bs_host=peer1.node.ip, bs_port=peer1.node.port, bs_id=peer1.node.id, _id=i)
        peers.append(new_peer)
        t = threading.Thread(target=new_peer.run) 
        t.start()
        threads.append(t)
    
    
    # Node 2**159
    peer5 = peers[4]
    peer2 = Peer(bs_host=peer5.node.ip, bs_port=peer5.node.port, bs_id=peer5.node.id, _id=2**159)
    print(f"Peer 2**159 routing table: {peer2.routing_table}")

    
    # Node_lookup on 2**159 from node 1
    x = peer1.iterative_node_lookup(2**159)
    print(f"Closest nodes found in network to 2**159: {x}")
    print(x)

        
    # Get routing info from node 1
    for t in threads:
        t.join()



    
    




def main():
    test_node_lookup()


if __name__ == "__main__":
    main()