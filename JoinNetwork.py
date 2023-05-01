#!/usr/bin/env python3
from Peer import Peer
import sys
import asyncio

def main(id=None, myport=None, ip=None, port=None):
    peer = Peer(_id=id, k=8)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(peer.listen(myport))
    if ip and port:
        loop.run_until_complete(peer.bootstrap([(ip, port)]))

    # Run forever
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    id, myport = int(sys.argv[1]), int(sys.argv[2]) 
    
    if len(sys.argv) < 4:
        main(id=None, myport=myport)
    else:
        bs_ip, bs_port = sys.argv[3], int(sys.argv[4])
        main(id=None, myport=myport, ip=bs_ip, port=bs_port)
        