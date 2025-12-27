import numpy as np
import pandas as pd
from spotify.spotify_requests import SearchRequests, UserRequests
from spotify.auth import Auth
from dotenv import load_dotenv

load_dotenv()

def get_recommendations(): # Daniel need to implement when cosign is ready
    songs_data = np.load('songs_data.npy')
    meta_df = pd.read_csv('songs_meta.csv')

def main():
    print("=== Spotipy ===")

    #connect to spotify
    username = input("Enter your Spotify username: ").strip()
    if not username:
        print("Username cannot be empty. Exiting.")
        return
    
    try:
        auth = Auth(username=username)
        spotify = auth.get_client()
        user_requests = UserRequests(spotify)
        search_requests = SearchRequests(spotify)
        current_user = user_requests.get_profile()

        print(f"\nSuccess! Connected as: {current_user['display_name']}")
        print(f"Spotify User ID: {current_user['id']}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Try deleting the .cache file and running again.")
        return
    

if __name__ == "__main__":
    main()