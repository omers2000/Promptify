from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

VALID_GENRES = [
    "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime",
    "black-metal", "bluegrass", "blues", "bossanova", "brazil", "breakbeat",
    "british", "cantopop", "chicago-house", "children", "chill", "classical",
    "club", "comedy", "country", "dance", "dancehall", "death-metal",
    "deep-house", "detroit-techno", "disco", "disney", "drum-and-bass",
    "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk", "forro",
    "french", "funk", "garage", "german", "gospel", "goth", "grindcore",
    "groove", "grunge", "guitar", "happy", "hard-rock", "hardcore",
    "hardstyle", "heavy-metal", "hip-hop", "holidays", "honky-tonk", "house",
    "idm", "indian", "indie", "indie-pop", "industrial", "iranian", "j-dance",
    "j-idol", "j-pop", "j-rock", "jazz", "k-pop", "kids", "latin", "latino",
    "malay", "mandopop", "metal", "metal-misc", "metalcore", "minimal-techno",
    "movies", "mpb", "new-age", "new-release", "opera", "pagode", "party",
    "philippines-opm", "piano", "pop", "pop-film", "post-dubstep",
    "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock",
    "r-n-b", "rainy-day", "reggae", "reggaeton", "road-trip", "rock",
    "rock-n-roll", "rockabilly", "romance", "sad", "salsa", "samba",
    "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep",
    "songwriter", "soul", "soundtracks", "spanish", "study", "summer",
    "swedish", "synth-pop", "tango", "techno", "trance", "trip-hop",
    "turkish", "work-out", "world-music"
]

class PlaylistSearchParams(BaseModel):
    # Request limit (Default: 20, Min: 1, Max: 100)
    limit: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Number of recommendations to return (1-100). Optional; defaults to 20."
    )

    # Seed values (Up to 5 total across all three)
    seed_artists: List[str] = Field(
        default_factory=list, 
        description=(
            "Optional List of artist names (not Spotify IDs) to serve as reference points for the recommendation algorithm. "
        )
    )
    
    seed_genres: List[str] = Field(
        default_factory=list,
        description=(
            "Optional List of genres for the recommendation algorithm. "
            f"Genres must be chosen from this set: {', '.join(VALID_GENRES)}. "
        )
    )

    seed_tracks: List[str] = Field(
        default_factory=list,
        description=(
            "Optional List of track names (not Spotify IDs) to serve as reference points for the recommendation algorithm. "
        )
    )

    # Acousticness
    min_acousticness: Optional[float] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Minimum acousticness (0=electronic, 1=acoustic). Optional; omit to leave unconstrained."
    )

    max_acousticness: Optional[float] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Maximum acousticness (0=electronic, 1=acoustic). Optional; omit to leave unconstrained."
    )

    target_acousticness: Optional[float] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Target acousticness (0=electronic, 1=acoustic). Optional; the system will try to match this value."
    )

    # Danceability
    min_danceability: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum danceability (0=least danceable, 1=most danceable). Optional; omit to leave unconstrained."
    )

    max_danceability: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Maximum danceability (0=least danceable, 1=most danceable). Optional; omit to leave unconstrained."
    )
    
    target_danceability: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Target danceability (0=least danceable, 1=most danceable). Optional; the system will try to match this value."
    )

    # Duration (ms)
    min_duration_ms: Optional[int] = Field(
        default=None,
        gt=0,
        description=(
            "Minimum track duration in milliseconds. Optional; Only set if the user requests a duration constraint, "
            "either a general preference (e.g., short/long songs) or a specific time limit."
        )
    )

    max_duration_ms: Optional[int] = Field(
        default=None,
        gt=0,
        description=(
            "Maximum track duration in milliseconds. Optional; Only set if the user requests a duration constraint, "
            "either a general preference (e.g., short/long songs) or a specific time limit."
        )
    )
    
    target_duration_ms: Optional[int] = Field(
        default=None,
        gt=0,
        description=(
            "Target track duration in milliseconds. Optional; Only set if the user requests a duration constraint, "
            "either a general preference (e.g., short/long songs) or a specific time limit."
        )
    )

    # Energy
    min_energy: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum energy (0=least energetic, 1=most energetic). Optional; omit to leave unconstrained."
    )

    max_energy: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Maximum energy (0=least energetic, 1=most energetic). Optional; omit to leave unconstrained."
    )
    
    target_energy: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Target energy (0=least energetic, 1=most energetic). Optional; the system will try to match this value."
    )

    # Instrumentalness
    min_instrumentalness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Minimum instrumentalness (0=most likely to contain vocals, "
            "1=least likely to contain vocals). Optional; omit to leave unconstrained."
        )
    )

    max_instrumentalness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Maximum instrumentalness (0=most likely to contain vocals, "
            "1=least likely to contain vocals). Optional; omit to leave unconstrained."
        )
    )

    target_instrumentalness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Target instrumentalness (0=most likely to contain vocals, "
            "1=least likely to contain vocals). Optional; the system will try to match this value."
        )
    )

    # Key (0-11)
    target_key: Optional[int] = Field(
        default=None,
        ge=0,
        le=11,
        description=(
            "Target musical key as an integer (0 = C, 1 = C#, …, 11 = B). "
            "Optional; set only if the user requests a specific key."
        )
    )

    # Liveness
    min_liveness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Minimum liveness (0=not live, 1=very live). Optional; Omit to leave unconstrained."
        )
    )
    max_liveness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Maximum liveness (0=not live, 1=very live). Optional; Omit to leave unconstrained."
        )
    )
    target_liveness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Target liveness (0=not live, 1=very live). Optional; The system will try to match this value."
        )
    )

    # Mode (0 or 1)
    target_mode: Optional[int] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Target mode (0 = minor, 1 = major). Optional; Set only if the user requests a specific mode."
        )
    )

    # Popularity (0-100)
    min_popularity: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description=(
            "Minimum popularity (0=least popular, 100=most popular). Optional; Omit to leave unconstrained."
        )
    )
    max_popularity: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description=(
            "Maximum popularity (0=least popular, 100=most popular). Optional; Omit to leave unconstrained."
        )
    )
    target_popularity: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description=(
            "Target popularity (0=least popular, 100=most popular). Optional; The system will try to match this value."
        )
    )

    # Speechiness
    min_speechiness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Minimum speechiness (0=least speech-like, 1=most speech-like). Optional; Omit to leave unconstrained."
        )
    )
    max_speechiness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Maximum speechiness (0=least speech-like, 1=most speech-like). Optional; Omit to leave unconstrained."
        )
    )
    target_speechiness: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Target speechiness (0=least speech-like, 1=most speech-like). Optional; The system will try to match this value."
        )
    )

    # Tempo (BPM)
    min_tempo: Optional[float] = Field(
        None,
        gt=0,
        description=(
            "Minimum tempo in beats per minute (BPM). Optional; Omit to leave unconstrained."
        )
    )
    max_tempo: Optional[float] = Field(
        None,
        gt=0,
        description=(
            "Maximum tempo in beats per minute (BPM). Optional; Omit to leave unconstrained."
        )
    )
    target_tempo: Optional[float] = Field(
        None,
        gt=0,
        description=(
            "Target tempo in beats per minute (BPM). Optional; The system will try to match this value."
        )
    )

    # Time Signature
    target_time_signature: Optional[int] = Field(
        None,
        ge=2,
        le=11,
        description=(
            "Target time signature (integer, e.g., 4 for 4/4). Optional; Set only if the user requests a time signature."
        )
    )

    # Valence
    min_valence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Minimum valence (0=least positive/happy, 1=most positive/happy). Optional; Omit to leave unconstrained."
        )
    )
    max_valence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Maximum valence (0=least positive/happy, 1=most positive/happy). Optional; Omit to leave unconstrained."
        )
    )
    target_valence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "Target valence (0=least positive/happy, 1=most positive/happy). Optional; The system will try to match this value."
        )
    )

    @model_validator(mode="after")
    def validate_seeds(self):
        """Validate that at least one type of seed is provided, and no more than 5 total seed values."""
        total_seeds = len(self.seed_artists) + len(self.seed_genres) + len(self.seed_tracks)
        if total_seeds == 0:
            raise ValueError("At least one of 'seed_artists', 'seed_genres', or 'seed_tracks' must be provided.")
        if total_seeds > 5:
            raise ValueError("The total number of seed values (across artists, genres, and tracks) may not exceed 5.")
        return self
    
    @model_validator(mode="after")
    def validate_genres(self):
        """Validate that the genres are valid."""
        for genre in self.seed_genres:
            if genre not in VALID_GENRES:
                raise ValueError(f"Invalid genre: {genre}")
        return self

    def to_spotipy_dict(self) -> dict:
        # Prepare the dictionary with only non-empty/non-None fields, and join lists as comma-separated
        data = self.model_dump()
        out = {}
        for k, v in data.items():
            if k in {"seed_artists", "seed_genres", "seed_tracks"}:
                if v:
                    out[k] = ",".join(v)
            elif v is not None and v != []:
                out[k] = v
        return out

