import pytest

from playlist_search_params import PlaylistSearchParams
from pydantic import ValidationError

# -------------------------
# Field Constraints Tests
# -------------------------

@pytest.mark.parametrize(
    "field_name, value",
    [
        ("min_popularity", -1),
        ("max_popularity", 101),
        ("min_danceability", -0.1),
        ("max_danceability", 1.1),
        ("min_acousticness", -0.01),
        ("max_acousticness", 1.05),
        ("target_energy", 2.0),
        ("min_valence", -1),
        ("max_valence", 1.5),
    ]
)
def test_field_constraints_raise_validation_error(field_name, value):
    kwargs = {
        "seed_artists": ["artist1"],  # required at least 1 seed
        field_name: value,
    }
    with pytest.raises(ValidationError):
        PlaylistSearchParams(**kwargs)


# -------------------------
# Seed Count Validation
# -------------------------

def test_validate_seeds_raises_if_zero_seeds():
    with pytest.raises(ValidationError) as exc_info:
        PlaylistSearchParams(
            seed_artists=[],
            seed_genres=[],
            seed_tracks=[]
        )
    assert "At least one of 'seed_artists', 'seed_genres', or 'seed_tracks' must be provided." in str(exc_info.value)


def test_validate_seeds_raises_if_more_than_five_seeds():
    # 2 + 2 + 2 = 6 seeds
    with pytest.raises(ValidationError) as exc_info:
        PlaylistSearchParams(
            seed_artists=["a1", "a2"],
            seed_genres=["rock", "pop"],
            seed_tracks=["t1", "t2"]
        )
    assert "may not exceed 5" in str(exc_info.value)


@pytest.mark.parametrize(
    "n_artists, n_genres, n_tracks",
    [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (2, 1, 0),
        (2, 0, 3),  # sum = 5
    ]
)
def test_validate_seeds_passes_when_valid_seed_count(n_artists, n_genres, n_tracks):
    valid_genres = ["rock", "pop", "jazz", "hip-hop", "country", "classical", "electronic", "metal"]
    seeds = {
        "seed_artists": [f"artist{i}" for i in range(n_artists)],
        "seed_genres": valid_genres[:n_genres],
        "seed_tracks": [f"track{i}" for i in range(n_tracks)]
    }
    # Should not raise
    PlaylistSearchParams(**seeds)


# -------------------------
# Genre Validation
# -------------------------

def test_validate_genres_with_invalid_genres():
    # Pick a genre that surely doesn't exist in VALID_GENRES
    with pytest.raises(ValidationError) as exc_info:
        PlaylistSearchParams(
            seed_artists=["artist1"],
            seed_genres=["notarealgenre"],
            seed_tracks=[]
        )
    assert "Invalid genre" in str(exc_info.value)


def test_validate_genres_with_all_valid_genres():
    # These genres must exist in VALID_GENRES per context
    valid_genres = ["rock", "pop"]
    obj = PlaylistSearchParams(
        seed_artists=["artist1"],
        seed_genres=valid_genres,
        seed_tracks=[]
    )
    assert obj.seed_genres == valid_genres


# -------------------------
# to_spotipy_dict Method Output
# -------------------------

def test_to_spotipy_dict_joins_lists_and_excludes_none():
    obj = PlaylistSearchParams(
        seed_artists=["artistA", "artistB"],
        seed_genres=["rock", "pop"],
        seed_tracks=["trackX"],
        min_popularity=50,
        max_acousticness=None,
        target_energy=None
    )
    out = obj.to_spotipy_dict()
    assert out["seed_artists"] == "artistA,artistB"
    assert out["seed_genres"] == "rock,pop"
    assert out["seed_tracks"] == "trackX"
    # Only min_popularity should exist, not any None
    assert out["min_popularity"] == 50
    assert "max_acousticness" not in out
    assert "target_energy" not in out

def test_to_spotipy_dict_skips_empty_lists():
    # Only artists, no genres/tracks
    obj = PlaylistSearchParams(
        seed_artists=["artistOnly"],
        seed_genres=[],
        seed_tracks=[],
        min_popularity=None,
    )
    out = obj.to_spotipy_dict()
    assert out["seed_artists"] == "artistOnly"
    assert "seed_genres" not in out
    assert "seed_tracks" not in out

