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

    # Optional Fields (defaults to None so they aren't sent if not requested)
    # negativeSeeds: Optional[List[str]] = Field(
    #     None, 
    #     min_length=1, max_length=5,
    #     description="List of Track IDs to avoid."
    # )
    
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
    
    # instrumentalness: Optional[float] = Field(
    #     None, ge=0, le=1, 
    #     description="Predicts whether a track contains no vocals (0.0 to 1.0)."
    # )
    
    # key: Optional[int] = Field(
    #     None, ge=0, le=11, 
    #     description="The key the track is in. -1 if no key detected."
    # )
    
    # liveness: Optional[float] = Field(
    #     None, ge=0, le=1, 
    #     description="Probability that the track was performed live (0.0 to 1.0)."
    # )
    
    # loudness: Optional[float] = Field(
    #     None, ge=-60, le=2, 
    #     description="Overall loudness of a track in decibels (dB)."
    # )
    
    # mode: Optional[int] = Field(
    #     None, ge=0, le=1, 
    #     description="Modality: 1 for Major, 0 for Minor."
    # )
    
    # speechiness: Optional[float] = Field(
    #     None, ge=0, le=1, 
    #     description="Presence of spoken words (0.0 to 1.0)."
    # )
    
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


# # ==========================================
# # 2. API MODEL (What ReccoBeats Receives)
# # ==========================================
# class ReccoRecommendationParams(AIRecommendationParams):
#     """
#     The final payload for the API.
#     Overrides the 'seed_track' logic with strict 'seeds' ID list.
#     """
    
#     # STRICT API REQUIREMENT: string[], size 1..5
#     seeds: List[str] = Field(
#         ..., 
#         min_length=1, 
#         max_length=5,
#         description="List of Spotify Track IDs. Required. Min 1, Max 5."
#     )
    
#     # App-controlled size (not AI controlled)
#     size: int = Field(NUMBER_OF_RECOMMENDATIONS, ge=1, le=100)

#     def to_query_params(self):
#         """
#         Formats data for the API request.
#         """
#         data = self.model_dump(exclude_none=True, exclude={'ai_choice_seed_track'})
#         return data