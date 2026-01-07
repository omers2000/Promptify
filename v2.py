import os
import numpy as np
import pandas as pd
from spotify.spotify_requests import SearchRequests, UserRequests
from spotify.auth import Auth
from llm.llm_prompt_interpreter import LlmPromptInterpreter
from data_class.recommendation_params import LocalSearchParams
from logic.search_engine import SearchEngine
from dotenv import load_dotenv

load_dotenv()

def _is_geminiKey_exist():
    if os.getenv("GEMINI_KEY") is None:
        raise Exception("Google Gemini API Key not found in environment variables.")
    
def _setup_gemini():
    _is_geminiKey_exist()
    return LlmPromptInterpreter(api_key=os.getenv("GEMINI_KEY"))

def get_gemini_recommendations():
    interpreter = _setup_gemini()

    # get playlist description from user
    print("Please enter a description for your new playlist:")
    playlist_description = input().strip()

    if not playlist_description:
        raise ValueError("Playlist description cannot be empty.")
    
    print("Analyzing prompt with Gemini...")
    ai_params_object = interpreter.interpret(
        user_prompt=playlist_description, 
        response_model=LocalSearchParams
    )
    return ai_params_object.get_search_data()

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
    
    try:
        params = get_gemini_recommendations() ## until here fixed for v2
        targets = params[0]
        weights = params[1]

        search_engine = SearchEngine()
        db_recommendations = search_engine.search_db(targets, weights)
        rec_track_ids = [track['track_id'] for track in db_recommendations]

        # create playlist
        playlist_name = input("Enter your new Spotify playlist name: ").strip()
        if not playlist_name:
            playlist_name = "My New Playlist"
        playlist = user_requests.create_playlist(
            name=playlist_name,
            songs=rec_track_ids)
            
        print("Playlist created successfully:", playlist["external_urls"]["spotify"])

    except FileNotFoundError as e: 
        # missing database file
        print(f"\n {e}")
    except ValueError as e:
        # Logic errors (e.g. empty lists)
        print(f"\nOperation Stopped: {e}")
    except Exception as e:
        # Other exceptions
        print(f"\nOperation Stopped: {e}")
    except Exception as e:
        # Unexpected crashes
        print(f"\nAn unexpected error occurred: {e}")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    
if __name__ == "__main__":
    main()