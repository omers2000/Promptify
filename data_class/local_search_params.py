from typing import Optional
from pydantic import BaseModel, Field

# ==========================================
# 1. CORE BUILDING BLOCK
# ==========================================
class WeightedFeature(BaseModel):
    """
    Represents a specific audio feature with a target value and an importance weight.
    Used by the Local Engine (Pipeline 2) to calculate weighted Euclidean distance.
    """
    value: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Target value normalized between 0.0 and 1.0."
    )
    weight: float = Field(
        default=1.0, 
        ge=0, 
        le=5, 
        description="Importance level: 0=Ignore, 1=Low, 3=High, 5=Critical/Must Have."
    )

# ==========================================
# 2. THE BRAIN (LLM OUTPUT STRUCTURE)
# ==========================================
class LocalSearchQueryParams(BaseModel):
    """
    Structure for Gemini's output to drive the Local Search Engine (Pipeline 2).
    It translates user intent into mathematical vectors (Target + Weight).
    """
    
    # --- Text Filter ---
    target_genre: Optional[str] = Field(
        None, 
        description=(
            "Optional. The exact genre name if specified (e.g., 'Pop', 'Rock', 'Jazz'). "
            "Acts as a strict pre-filter before calculating distance."
        )
    )

    # --- Numeric Features ---
    # Descriptions are optimized for LLM understanding of Spotify's audio features.
    
    danceability: Optional[WeightedFeature] = Field(
        None, 
        description="How suitable a track is for dancing. 0.0 = Not danceable, 1.0 = Club/Party ready."
    )
    
    energy: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Intensity and activity measure. "
            "1.0 = Fast, loud, noisy (e.g., Death Metal). "
            "0.0 = Calm, slow, quiet (e.g., Bach Prelude)."
        )
    )
    
    valence: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Musical positiveness/Mood. "
            "1.0 = Happy, cheerful, euphoric. "
            "0.0 = Sad, depressing, angry."
        )
    )
    
    speechiness: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Presence of spoken words. "
            "High (>0.66) = Podcast/Spoken Word. "
            "Mid (0.33-0.66) = Rap/Hip-Hop. "
            "Low (<0.33) = Melodic singing (Music)."
        )
    )
    
    acousticness: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Confidence measure of how acoustic the track is. "
            "1.0 = Unplugged/Organic instruments. "
            "0.0 = Electronic/Synthesized."
        )
    )
    
    instrumentalness: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Predicts if a track contains no vocals. "
            "High (>0.5) = Instrumental/Background music (Good for study/focus). "
            "Low = Contains vocals."
        )
    )
    
    tempo: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Relative speed/pace normalized to 0-1 range. "
            "0.0 = Very Slow (~50 BPM). "
            "0.5 = Moderate (~120 BPM). "
            "1.0 = Very Fast (~200+ BPM)."
        )
    )
    
    popularity: Optional[WeightedFeature] = Field(
        None, 
        description=(
            "Track popularity normalized. "
            "0.0 = Underground/Indie discoveries. "
            "1.0 = Mainstream global hits."
        )
    )

    # --- Explainability ---
    reasoning: str = Field(
        ..., 
        description="Brief explanation of why these specific values and weights were chosen based on the user prompt."
    )