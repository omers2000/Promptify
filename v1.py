from spotify.auth import Auth
from spotify.spotify_requests import UserRequests, SearchRequests
from rb.rb_functions import get_recommendations_ids_by_params

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
    # params = get_params_from_model(playlist_description) ## Daniel needs to implement this function
    params = {'track_name': 'Espresso', 'artist_name': 'Sabrina Carpenter', 'acousticness': 0.1, 'energy': 0.8, 'valence': 0.5, 'featureWeight': 3.0, 'size': 20}

    # get recommendations
    seed_spot_id = search_requests.get_id_by_song(params['track_name'], params['artist_name'])
    params['seeds'] = seed_spot_id
    params.pop('track_name')
    params.pop('artist_name')
    rec_track_ids = get_recommendations_ids_by_params(params)

    # create playlist
    playlist = user_requests.create_playlist(
        name="My New Playlist",
        songs=rec_track_ids)
    print("Playlist created successfully:", playlist["external_urls"]["spotify"])

if __name__ == "__main__":
    main()