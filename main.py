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

    try:
        profile = user_requests.get_profile()
        tracks = user_requests.get_top_tracks()

        # res_by_desc = search_requests.search_track("""artist: Ed Sheeran year: 2015-2020""")
        
        # print("Connected as:", profile["display_name"])
        # print("User ID:", profile["id"], "\n")
        # print("Top Tracks:", [item["name"] for item in tracks["items"]])
        # print("Search Results for artists: ed sheeran year: 2015-2020", [item["name"] for item in res_by_desc["tracks"]["items"]])
        playlist = user_requests.create_playlist(
            name="My New Playlist",
            public=False,
            songs=[track["uri"] for track in tracks["items"]]
        )

    except Exception as exc:
        print("Authentication failed:", exc)


if __name__ == "__main__":
    main()