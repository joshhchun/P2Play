import hashlib
from time import monotonic_ns
from typing import Union, Iterable


class KadFile:
    '''
    A class that represents a kad-file.
    '''
    def __init__(self, dict_kad_file: dict):
        self.construct_kad_file(dict_kad_file)
    
    def construct_kad_file(self, dict_kad_file: dict):
        '''
        Constructs a kad-file from a dictionary.
        '''
        if not self.correct_format(dict_kad_file):
            raise ValueError('Incorrect format for kad-file')
        
        self.version     = dict_kad_file['version']
        self.song_name   = dict_kad_file['song_name']
        self.artist_name = dict_kad_file['artist_name']
        self.providers   = dict_kad_file['providers']
        self.id          = dict_kad_file["id"]
    
    def correct_format(self, dict_kad_file: dict) -> bool:
        '''
        Checks if all the correct fields are present in the kad-file.
        '''
        # Check if version, song_name, song_artist, and providers are present
        fields = ['version', 'song_name', 'artist_name', 'providers']
        return all(field in dict_kad_file for field in fields)
    
    def add_provider(self, provider):
        '''
        Adds a provider server addr to the kad-file.
        '''
        self.providers.append((provider.node.id, (provider.node.ip, provider.node.port)))
        self.version += 1

    @property
    def key(self) -> int:
        '''
        The hashed key of the song id.
        '''
        return int(hashlib.sha1(self.song_id.encode()).hexdigest(), 16)
    
    @property
    def dict(self) -> dict:
        '''
        Returns a dictionary representation of the kad-file.
        '''
        return {
            'version'    : self.version,
            'song_name'  : self.song_name,
            'artist_name': self.artist_name,
            'providers'  : self.providers,
            'id'         : self.id
        }
    
    @property
    def song_id(self) -> str:
        return f"{self.song_name}-{self.artist_name}"
    
    def __repr__(self):
        string = []
        string.append(f" Version     : {self.version}\n")
        string.append(f"\t\tSong Name   : {self.song_name}\n")
        string.append(f"\t\tArtist Name : {self.artist_name}\n")
        _id = self.id if len(str(self.id)) <= 10 else str(self.id)[:10] + '...'
        string.append(f"\t\tSong ID     : {_id}\n")
        string.append(f"\t\tProviders   : \n")
        for provider in self.providers:
            string.append(f"\t\t\t{provider}\n")
        return ''.join(string)


class SongStorage:
    '''
    Storage class for kad-files
    '''
    def __init__(self):
        self.data = {}
    
    def add(self, song_key: int, kad_file: KadFile):
        '''
        Add a kad-file to the storage with a timestamp
        Params: song_id (int), kad_file (KadFile)
        Returns: None
        '''
        self.data[song_key] = (kad_file, monotonic_ns())
    
    def get(self, song_key: int) -> Union[KadFile, None]:
        '''
        Retreive a kad-file from the storage.
        Params: song_id (int)
        Returns: kad_file (KadFile)
        '''
        if song_key in self.data:
            return self.data[song_key][0]
        return None
    
    def get_time(self, song_key: int) -> Union[int, None]:
        '''
        Retreive the timestamp of a kad-file from the storage.
        Params: song_id (int)
        Returns: timestamp (int)
        '''
        if song_key in self.data:
            return self.data[song_key][1]
        return None
    

    def get_republish_list(self, refresh_time: int) -> Iterable[tuple[int, KadFile]]:
        '''
        Returns a list of (song_key: kad-files) that are older than refresh_time

        # Sec 2.5 optimization
        '''
        min_time = monotonic_ns() - (refresh_time * 10**9)
        for song_key, (kad_file, timestamp) in self.data.items():
            if timestamp < min_time:
                yield song_key, kad_file
    
    def __repr__(self):
        string = ['SongStorage:\n']
        for song_key, (kad_file, _) in self.data.items():
            if len(str(song_key)) > 10:
                song_key = str(song_key)[:10] + '...'
            string.append(f"{song_key}: {kad_file}")
        return ''.join(string)
        
