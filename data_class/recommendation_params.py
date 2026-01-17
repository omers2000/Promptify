from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from config.model_consts import NUMBER_OF_RECOMMENDATIONS, FEATURE_WEIGHT, LLM_NUM_SEEDS, FEATURE_ORDER, MIN_POPULARITY

# ==========================================
# 1. Building Block: SEEDS (Only for Pipeline 1)
# ==========================================
class SeedInfo(BaseModel):
    track_name: str = Field(..., description="The name of the track")
    artist_name: str = Field(..., description="The name of the artist")

class SeedParams(BaseModel):
    seeds: List[SeedInfo]= Field(
        ..., 
        min_items=1,
        max_length=LLM_NUM_SEEDS,
        description=(
            f"A list of EXACTLY {LLM_NUM_SEEDS} objects containing 'track_name' and 'artist_name'. "
            f"If the user provides fewer than {LLM_NUM_SEEDS} tracks, you MUST supplement the list "
            f"with additional similar tracks to reach a total of {LLM_NUM_SEEDS}. "
            f"If the user provides more than {LLM_NUM_SEEDS}, select the top {LLM_NUM_SEEDS} most relevant. "
            f"If no tracks are specified, pick {LLM_NUM_SEEDS} tracks. Base on the described mood/genre/track requests."
        )
    )


# ==========================================
# 2. Building Block: TARGET VALUES (For Both Pipelines)
# ==========================================
class AudioFeatures(BaseModel):
    """
    Defines the target values (0-1 or BPM) for the tracks.
    Used for filtering or searching.
    """
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
        None, ge=MIN_POPULARITY, le=100, 
        description=(
            f"Track popularity. The scale is 0-100 (0 = least popular, 100 = most popular), "
            f"but you MUST output a value between {MIN_POPULARITY} and 100."            
        )
    )


# ==========================================
# 3. Building Block: WEIGHTS (For Ranking/Weighted Search)
# ==========================================
class FeatureWeights(BaseModel):
    """
    Defines the importance (weight) of each feature based on the user's prompt.
    0.0 = Not important / Don't care.
    1.0 = Very important / Critical constraint.
    """
    acousticness_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the acousticness target.")
    danceability_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the danceability target.")
    energy_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the energy target.")
    tempo_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the tempo target.")
    valence_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the valence target.")
    popularity_weight: float = Field(0.5, ge=0, le=1, description="Importance of matching the popularity target.")

    def get_weights_vector(self) -> List[float]:
        """Returns the weights as a list in the order of FEATURE_ORDER."""
        # Dynamic mapping based on names in FEATURE_ORDER + the suffix '_weight'
        return [getattr(self, f"{f}_weight", 0.0) for f in FEATURE_ORDER]


# ==========================================
# 4. FINAL MODELS (What you send to Gemini)
# ==========================================

# Pipeline 2: Local Data (No Seeds + Features + Weights for vector search)
class LocalSearchParams(BaseModel):
    target_features: AudioFeatures
    feature_weights: FeatureWeights

    def get_search_data(self) -> Tuple[List[float], List[float]]:
        """
        Returns two synchronized vectors: (Targets, Weights).
        Handles the issue where a feature is None by setting its weight to 0.
        This prevents math errors during distance calculation.
        """
        targets = []
        weights = []

        for feature in FEATURE_ORDER:
            val = getattr(self.target_features, feature)
            weight = getattr(self.feature_weights, f"{feature}_weight")

            if val is None:
                # If target is None, we cannot calculate distance.
                # Treat this feature as irrelevant (weight 0).
                targets.append(0.0) # Placeholder value
                weights.append(0.0) # Zero weight = ignore this dimension
            else:
                targets.append(float(val))
                weights.append(float(weight))
        
        return targets, weights

# Pipeline 1: External API (Needs Seeds + Features + Weights for post-sorting)
class ReccoBeatsParams(LocalSearchParams):
    seed_params: SeedParams

    def to_query_params(self) -> Dict[str, Any]:
        """
        Flattens the structure for the external API request.
        Only includes target values (seeds and features), ignores weights here.
        """
        # 1. Get seed data
        params = self.seed_params.model_dump(exclude_none=True) # returns {'seeds': [...]}
        
        # 2. Get feature values (flattened)
        features = self.target_features.model_dump(exclude_none=True)
        
        # 3. Merge
        params.update(features)
        params['size'] = NUMBER_OF_RECOMMENDATIONS
        return params
