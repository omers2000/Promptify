import os
import spotipy
from dotenv import load_dotenv
from config.spotify_consts import REDIRECT_URI, SCOPE
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler

load_dotenv()

class Auth():
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: str):
        """
        Initializes the Auth manager for a specific user.
        
        Args:
            client_id (str, optional): Overrides the env variable if provided.
            client_secret (str, optional): Overrides the env variable if provided.
            redirect_uri (str): The redirect URI for Spotify OAuth.
            scope (str): The scope of permissions for Spotify OAuth.
        """
        self.client_id = client_id
        self.client_secret = client_secret

        if not self.client_id or not self.client_secret:
            raise ValueError("No Client ID or Secret found. Please set them in your .env file.")

        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_handler=MemoryCacheHandler(), # Essential for Cloud persistence
            show_dialog=True)
        
    def get_client(self, auth: spotipy.Spotify) -> spotipy.Spotify:
        """
        Return an authenticated Spotipy client.
        """
        return spotipy.Spotify(auth_manager=auth)