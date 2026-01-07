import os
from typing import List, Dict
from spotify.auth import Auth
from spotify.spotify_requests import UserRequests, SearchRequests
from rb.rb_functions import get_recommendations_ids_by_params, get_audio_features
from data_class.recommendation_params import ReccoBeatsParams
from llm.llm_prompt_interpreter import LlmPromptInterpreter
from config.model_consts import DEFAULT_PLAYLIST_LENGTH
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
    return interpreter.interpret(
        user_prompt=playlist_description, 
        response_model=ReccoBeatsParams
    )

def get_top_songs(ai_params_object, rec_track_ids: List[Dict], top_n: int) -> list:
    """Returns the top N track IDs from the recommendation results."""
    top_songs = []
    target_vector, weights_vector = ai_params_object.get_search_data()
    candidates_list = [get_audio_features(item) for item in rec_track_ids]
    sorted_songs = SearchEngine.rank_reccobeats_candidates(candidates_list, target_vector, weights_vector)
    for song in sorted_songs[:top_n]:
        top_songs.append(song["spot_id"])
    return top_songs

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
        ai_params_object = get_gemini_recommendations()
        params = ai_params_object.to_query_params()
        seeds = params.get("seeds")

        print(f"\nAI Suggestion Strategy: {params}")
        print("\n--- Resolving Seeds on Spotify ---")

        # get recommendations
        valid_seed_ids = []
        for seed in seeds:
            track_name = seed.get('track_name')
            artist_name = seed.get('artist_name')

            seed_spot_id = search_requests.get_id_by_song(track_name, artist_name)

            if seed_spot_id:
                print(f"Found: {track_name} by {artist_name}")
                valid_seed_ids.append(seed_spot_id)
            else:
                print(f"Warning: Spotify could not find '{track_name}'. Skipping.")

        if not valid_seed_ids:
            raise ValueError("Spotify could not find ANY of the seed songs suggested by Gemini.")

        params['seeds'] = ",".join(valid_seed_ids)
        
        print(f"\nFetching recommendations based on {len(valid_seed_ids)} seeds...")
        rec_track_ids = get_recommendations_ids_by_params(params)

        if not rec_track_ids:
            raise ValueError("Recommendation API returned no tracks (result was empty).")
        
        top_rec_ids = get_top_songs(ai_params_object, rec_track_ids, top_n=DEFAULT_PLAYLIST_LENGTH)

        # create playlist
        playlist_name = input("Enter your new Spotify playlist name: ").strip()
        if not playlist_name:
            playlist_name = "My New Playlist"
        playlist = user_requests.create_playlist(
            name=playlist_name,
            songs=top_rec_ids)
            
        # add seeds to playlist
        for seed_id in params['seeds'].split(","):
            user_requests.add_track_to_playlist(playlist_id=playlist["id"], track_id=seed_id)

        print("Playlist created successfully:", playlist["external_urls"]["spotify"])

    except ValueError as ve:
        # Logic errors (e.g. empty lists)
        print(f"\nOperation Stopped: {ve}")
    except Exception as e:
        # Unexpected crashes
        print(f"\nAn unexpected error occurred: {e}")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")


if __name__ == "__main__":
    main()
