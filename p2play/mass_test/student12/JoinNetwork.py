#!/usr/bin/env python3
import sys
sys.path.append("../../")
from Peer import Peer
import sys
import asyncio

def main(id=None, myip=None, myport=None, kad_path=None, ip=None, port=None):
    peer = Peer(_id=id, kad_path=kad_path)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(peer.listen(myport, myip))
    if ip and port:
        loop.run_until_complete(peer.bootstrap([(ip, port)]))

    # Run forever
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    id, myip, myport, path = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4]
    
    if len(sys.argv) < 6:
        main(id=None, myip=myip, myport=myport, kad_path=path)
    else:
        bs_ip, bs_port = sys.argv[5], int(sys.argv[6])
        main(id=None, myport=myport, myip=myip, kad_path=path, ip=bs_ip, port=bs_port)
        
