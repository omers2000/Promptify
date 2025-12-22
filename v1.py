import os
from spotify.auth import Auth
from spotify.spotify_requests import UserRequests, SearchRequests
from rb.rb_functions import get_recommendations_ids_by_params
from llm.llm_prompt_interpreter import LlmPromptInterpreter
from dotenv import load_dotenv

load_dotenv()
    
def _is_geminiKey_exist():
    if os.getenv("GEMINI_KEY") is None:
        raise Exception("Google Gemini API Key not found in environment variables.")
    
def _setup_gemini():
    # print("Please enter your Google Gemini API Key:")
    # google_api_key = input().strip()
    print("Analyzing prompt with Gemini...")
    # return LlmPromptInterpreter(api_key=google_api_key)
    _is_geminiKey_exist()
    return LlmPromptInterpreter(api_key=os.getenv("GEMINI_KEY"))

def get_gemini_recommendations():
    # get playlist description from user
    print("Please enter a description for your new playlist:")
    playlist_description = input().strip()

    interpreter = _setup_gemini()
    ai_params_object = interpreter.interpret(playlist_description)
    return ai_params_object.to_query_params()


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

        try:
            params = get_gemini_recommendations()
            seeds = params.get("seeds")
            for seed in seeds:
                print(f"Selected Seed: {seed.get('track_name')} by {seed.get('artist_name')}")
            print(f"Track recommendation params: {params}")

            # seeds = {'track_name': 'September', 'artist_name': 'Earth, Wind & Fire'}
            # params = {'seeds': seeds, 'valence': 0.8, 'popularity': 80, 'featureWeight': 5.0, 'size': 40}

            # get recommendations
            seeds_string = ""
            for seed in seeds:
                seed_spot_id = search_requests.get_id_by_song(seed['track_name'], seed['artist_name'])
                seeds_string += seed_spot_id + ","
            params['seeds'] = seeds_string.rstrip(",")
            rec_track_ids = get_recommendations_ids_by_params(params)

            # create playlist
            playlist = user_requests.create_playlist(
                name="My New Playlist",
                songs=rec_track_ids)
            
            # add seeds to playlist
            for seed_id in params['seeds'].split(","):
                user_requests.add_track_to_playlist(playlist_id=playlist["id"], track_id=seed_id)
            print("Playlist created successfully:", playlist["external_urls"]["spotify"])

        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Try deleting the .cache file and running again.")


if __name__ == "__main__":
    main()