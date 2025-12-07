from spotify.auth import Auth
from spotify.spotify_requests import UserRequests, SearchRequests
from rb.rb_functions import get_recommendations_ids_by_params
from llm.llm_prompt_interpreter import LlmPromptInterpreter

def _get_client_credentials():
    print("Please enter your Spotify Client ID:")
    client_id = input().strip()
    print("Please enter your Spotify Client Secret:")
    client_secret = input().strip()
    return Auth(
        client_id=client_id,
        client_secret=client_secret,
    )

def main():
    #connect to spotify
    auth = _get_client_credentials()
    spotify = auth.get_client()
    user_requests = UserRequests(spotify)
    search_requests = SearchRequests(spotify)
    print("Please allow the needed permissions and copy the redirect URL from your browser after authentication:")
    user_requests.get_profile()  # Trigger authentication flow

    # get playlist description from user
    print("Please enter a description for your new playlist:")
    playlist_description = input().strip()

    # Setup Gemini
    print("Please enter your Google Gemini API Key:")
    google_api_key = input().strip()
    print("Analyzing prompt with Gemini...")
    interpreter = LlmPromptInterpreter(api_key=google_api_key)

    try:
        ai_params_object = interpreter.interpret(playlist_description)
        params = ai_params_object.to_query_params()
        seeds = params.get("seeds")
        print(f"Selected Seed: {seeds.get('track_name')} by {seeds.get('artist_name')}")
        print(f"Track recommendation params: {params}")

    except Exception as e:
        print(f"An error occurred: {e}")

    # get recommendations
    seed_spot_id = search_requests.get_id_by_song(seeds['track_name'], seeds['artist_name'])
    params['seeds'] = seed_spot_id
    # params.pop('track_name')
    # params.pop('artist_name')
    rec_track_ids = get_recommendations_ids_by_params(params)

    # create playlist
    playlist = user_requests.create_playlist(
        name="My New Playlist",
        songs=rec_track_ids)
    print("Playlist created successfully:", playlist["external_urls"]["spotify"])

if __name__ == "__main__":
    main()