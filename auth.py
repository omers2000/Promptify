import spotipy
from config import connection
from spotipy.oauth2 import SpotifyOAuth
class Auth():
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=connection.REDIRECT_URI,
            scope=connection.SCOPE,
            open_browser=True)
        
    def get_client(self) -> spotipy.Spotify:
        """
        Return an authenticated Spotipy client.
        """
        return spotipy.Spotify(auth_manager=self.auth_manager)