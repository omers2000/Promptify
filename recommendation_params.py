from typing import Optional, List, Dict
from pydantic import BaseModel, Field

NUMBER_OF_RECOMMENDATIONS = 20

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
        description="A dictionary that MUST contain two key-value pairs: 'track_name' (string) and 'artist_name' (string). The model must output both keys."
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
    
    featureWeight: Optional[float] = Field(
        None, ge=1, le=5, 
        description="Scales the influence of audio feature queries by multiplying each feature before averaging."
    )

    def to_query_params(self):
        """
        Converts the model to a dictionary suitable for the requests library,
        removing keys that were not set (None).
        """
        # exclude_none=True removes all the optional fields we didn't use
        params_dict =  self.model_dump(exclude_none=True)
        params_dict['size'] = NUMBER_OF_RECOMMENDATIONS
        return params_dict
