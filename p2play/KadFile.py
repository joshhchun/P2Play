from Peer import Peer

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
            # TODO: Figure out what to do if there is an error
            raise ValueError('Incorrect format for kad-file')
        
        self.version     = dict_kad_file['version']
        self.song_name   = dict_kad_file['song_name']
        self.artist_name = dict_kad_file['artist_name']
        self.providers   = dict_kad_file['providers']
    
    def correct_format(self, dict_kad_file: dict) -> bool:
        '''
        Checks if all the correct fields are present in the kad-file.
        '''
        # Check if version, song_name, song_artist, and providers are present
        fields = ['version', 'song_name', 'artist_name', 'providers']
        return all(field in dict_kad_file for field in fields)
    
    def add_provider(self, provider: Peer):
        '''
        Adds a provider server addr to the kad-file.
        '''
        self.providers.append((provider.node.id, provider.server_addr))
    
    @property
    def dict(self):
        '''
        Returns a dictionary representation of the kad-file.
        '''
        return {
            'version'    : self.version,
            'song_name'  : self.song_name,
            'artist_name': self.artist_name,
            'providers'  : self.providers
        }