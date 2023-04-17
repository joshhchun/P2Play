from Peer import Peer
import asyncio
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

server = Peer()
def create_bootstrap_node():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.listen(9000))
    print(server.get_info())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

def main():
    print("Starting server...")
    create_bootstrap_node()

if __name__ == '__main__':
    main()