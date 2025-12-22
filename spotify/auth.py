import os
import spotipy
from dotenv import load_dotenv
from config.spotify_consts import REDIRECT_URI, SCOPE
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

class Auth():
    def __init__(self, username: str, client_id: str = None, client_secret: str = None):
        """
        Initializes the Auth manager for a specific user.
        
        Args:
            username (str): A unique identifier for the user (to create their specific cache file).
            client_id (str, optional): Overrides the env variable if provided.
            client_secret (str, optional): Overrides the env variable if provided.
        """
        self.client_id = client_id or os.getenv("SP_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SP_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("No Client ID or Secret found. Please set them in your .env file.")
        
        # This creates a file like .spotify_cache_dan, .spotify_cache_alice, etc.
        self.cache_path = f".spotify_cache_{username}"

        # Check if the file exists BEFORE we start the auth manager
        if os.path.exists(self.cache_path):
            print(f"\nWelcome back, {username}! Connecting in the background...")
        else:
            print(f"\n--- NEW USER DETECTED: {username} ---")
            print("1. A web browser will open automatically.")
            print("2. Please log in to Spotify and click 'Agree'.")
            print("3. Once done, copy the URL and return here.")
            print("---------------------------------------")
            input("Press Enter to open browser and login...")

        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,
            cache_path=self.cache_path)
        
    def get_client(self) -> spotipy.Spotify:
        """
        Return an authenticated Spotipy client.
        """
        return spotipy.Spotify(auth_manager=self.auth_manager)