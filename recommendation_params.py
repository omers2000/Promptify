from typing import Optional, Dict
from pydantic import BaseModel, Field

NUMBER_OF_RECOMMENDATIONS = 20
FEATURE_WEIGHT = 5.0

# ==========================================
# 1. AI MODEL (What Gemini Sees)
# ==========================================
class AIRecommendationParams(BaseModel):
    """
    Data model for ReccoBeats Recommendation API parameters.
    Used to structure LLM outputs and validate data before API calls.
    """
    
    # Required Fields
    seeds: Dict[str, str] = Field(
        ..., 
        description=(
            "Dictionary with two required keys: 'track_name' (string) and 'artist_name' (string). "
            "Represents the seed track for recommendations. "
            "If a track is not specified by the user, select one based on their described mood or genre."
        )
    )
    
    acousticness: Optional[float] = Field(
        None, ge=0, le=1, 
        description="Confidence measure from 0.0 to 1.0 of how acoustic the track is."
    )
    
    danceability: Optional[float] = Field(
        None, ge=0, le=1, 
        description="How suitable a track is for dancing (0.0 to 1.0)."
    )
    
    energy: Optional[float] = Field(
        None, ge=0, le=1, 
        description="Intensity and liveliness (0.0 to 1.0)."
    )
    
    tempo: Optional[float] = Field(
        None, ge=0, le=250, 
        description="Estimated tempo in BPM."
    )
    
    valence: Optional[float] = Field(
        None, ge=0, le=1, 
        description="Musical positiveness (0.0 = sad, 1.0 = happy)."
    )
    
    popularity: Optional[int] = Field(
        None, ge=0, le=100, 
        description="Track popularity (0-100)."
    )

    @property
    def track_name(self) -> str:
        """Retrieves the track name from the nested seeds dictionary."""
        # Use .get() for safety, though Pydantic should ensure the key exists.
        return self.seeds.get('track_name', '')

    @property
    def artist_name(self) -> str:
        """Retrieves the artist name from the nested seeds dictionary."""
        return self.seeds.get('artist_name', '')

    def to_query_params(self):
        """
        Converts the model to a dictionary suitable for the requests library,
        removing keys that were not set (None).
        """
        # exclude_none=True removes all the optional fields we didn't use
        params_dict =  self.model_dump(exclude_none=True)
        params_dict['size'] = NUMBER_OF_RECOMMENDATIONS
        params_dict['featureWeight'] = FEATURE_WEIGHT
        return params_dict
