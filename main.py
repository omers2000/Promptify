from auth import Auth
from spotify_requests import UserRequests, SearchRequests
from config.connection import CLIENT_ID, CLIENT_SECRET

def main():
    auth = Auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )
    spotify = auth.get_client()

    user_requests = UserRequests(spotify)
    search_requests = SearchRequests(spotify)

    # item_struct = {
    #     "name": "Track Name",
    #     "id": "Track ID",
    #     "artists": [],}

    try:
        profile = user_requests.get_profile()
        tracks = user_requests.get_top_tracks()

        search_test = search_requests.get_id_by_song("Shape of you", "Ed Sheeran")
        print("Track ID for 'Shape of you' by Ed Sheeran:", search_test)

        # Search for tracks and parse results
        # search_results = search_requests.search_track("track:Shape of you artist:Ed Sheeran", limit=5)
        # parsed_tracks = search_requests.parse_tracks(search_results)
        
        # print("Search Results for 'Shape of you':")
        # print("=" * 50)
        # for track in parsed_tracks:
        #     print(track)
        #     print("-" * 50)
        
        # print("Connected as:", profile["display_name"])
        # print("User ID:", profile["id"], "\n")
        # print("Top Tracks:", [item["name"] for item in tracks["items"]])
        # playlist = user_requests.create_playlist(
        #     name="My New Playlist",
        #     public=False,
        #     songs=[track["uri"] for track in tracks["items"]]
        # )

    except Exception as exc:
        print("Authentication failed:", exc)


if __name__ == "__main__":
    main()