#!/usr/bin/env python3
from Peer import Peer
import threading

def test_node_lookup():
    port = 9000
    threads = []
    peers   = []
    peer1   = Peer(_id=1)
    peers.append(peer1)

    # Run the node in a thread
    t1 = threading.Thread(target=peer1.listen(port))
    t1.start()
    threads.append(t1)

    old = peer1
    # Put nodes 1-35 in the routing table of node 1 all in different threads
    for i in range(2, 151):
        new_peer = Peer(_id=i)
        peers.append(new_peer)
        t = threading.Thread(target=new_peer.listen(port + i))
        t.start()
        threads.append(t)
        old = new_peer

    print("-------\n")

    print("Peer 150 routing table:")
    print(peers[149].routing_table)


    """
    def run(self) -> None:
        for file in select.select(things, [], [])[0]:
            


    def callback(results: List[Peer]) -> None:
        ...

    iterative_node_lookup(target_id, callback)
    """



    # print(f"peer4: {peer4.routing_table}")
    # x = peer4.iterative_node_lookup(4)
    # print(f"x: {x}")
    # print(f"Closest nodes found in network to 2**159: {x}")

    # iterative_node_lookup(number: int, callback: Callable[]) -> None
    # Maybe make it immediately return and then have a function like
    # peer.serve() That runs forever `select`


def main():
    test_node_lookup()


if __name__ == "__main__":
    main()
