# P2Play

# How to run
## First node in network
If you are the first node in the network (no bootstraps), you can start your peer by doing the following:
``` bash
python3 client.py --ip=<ip> --port=<port>
```
This will start the interactive shell UI, where you have the following commands:
- `get <Song Name> <Artist Name>`, which downloads a song from the network
- `put <Song Name> <Artist Name>`, which uploads a song to the network
- `table`, which shows the state of the peer's routing table
- `info`, which outputs the peers ip, port, and ID
- **Note that `<Song Name>` and `<Artist Name>` should be camel cased with no spaces**

## Not first node in the network
If you are not the first node in the network, you will need the address of a node already in the network to join (bootstrap). You can start your peer by doing the following:
``` bash
python3 client.py --ip=<ip> --port=<port> --b=<bootstraps>
```
Note that the `<bootstraps>` should be in the following form
- `bshost1:port1,bshost2:port2,bshost3:port3...`

# Uploading / Storing Files
- After downloading a song from the network, the song will be stored in a `kad_files` directory under the `p2play` directory in the repo. This directory will automatically be created if it does not exist.
- To upload songs to the network, the user should create a directory called `kad_files` under the sub `p2play` directory if they do not have one already. They should then move any songs they want to put on the network in this directory. The user must rename the songs to fit the name scheme of P2Play, (e.g. `SongName - ArtistName.kad`)
