import spotipy
from typing import List
from dataclasses import dataclass


# @dataclass
# class Track:
#     """Data structure for track information"""
#     name: str
#     id: str
#     artists: List[dict]  # List of {name, id}
    
#     def __str__(self) -> str:
#         artists_str = ", ".join([f"{artist['name']} ({artist['id']})" for artist in self.artists])
#         return f"Track: {self.name} (ID: {self.id})\nArtists: {artists_str}"
    
#     def to_dict(self) -> dict:
#         return {
#             "name": self.name,
#             "id": self.id,
#             "artists": self.artists
#         }


class UserRequests:
    """User-related Spotify API requests

    Accepts a `spotipy.Spotify` client instance (returned by `Auth.get_client()`).
    """
    def __init__(self, spotify_client: spotipy.Spotify):
        self._client = spotify_client

    def get_profile(self) -> dict:
        return self._client.current_user()

    def get_top_tracks(self, limit: int = 10) -> list:
        return self._client.current_user_top_tracks(limit=limit)

    def get_saved_tracks(self, limit: int = 20) -> list:
        return self._client.current_user_saved_tracks(limit=limit)
    
    def create_playlist(self, name: str, public: bool = False, songs: List[str] = []) -> dict:
        user_id = self._client.current_user()["id"]
        playlist = self._client.user_playlist_create(user=user_id, name=name, public=public)
        if songs:
            self._client.playlist_add_items(playlist_id=playlist["id"], items=songs)
        return playlist


class SearchRequests:
    """Search-related Spotify API requests"""
    def __init__(self, spotify_client: spotipy.Spotify):
        self._client = spotify_client

    def search_track(self, query: str, limit: int = 10) -> dict:
        return self._client.search(q=query, type='track', limit=limit)

    def search_artist(self, query: str, limit: int = 10) -> dict:
        return self._client.search(q=query, type='artist', limit=limit)
    
    def get_id_by_song(self, song_name: str, artist_name: str) -> str:
        query = f"track:{song_name} artist:{artist_name}"
        results = self._client.search(q=query, type='track', limit=1)
        items = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]["id"]
        return ""
    
    # def parse_tracks(self, search_results: dict) -> List[Track]:
    #     """Parse search results into Track objects"""
    #     tracks = []
    #     for item in search_results.get("tracks", {}).get("items", []):
    #         track = Track(
    #             name=item.get("name"),
    #             id=item.get("id"),
    #             artists=[{"name": artist["name"], "id": artist["id"]} for artist in item.get("artists", [])]
    #         )
    #         tracks.append(track)
    #     return tracks