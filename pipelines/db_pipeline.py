"""
Pipeline V2: Database-based recommendations using local cosine search
Extracted from v2.py for use in the Streamlit app.
"""

from data_class.recommendation_params import LocalSearchParams
from logic.search_engine import SearchEngine
from config.model_consts import DEFAULT_PLAYLIST_LENGTH
from pipelines.shared import get_gemini_interpretation


def run_pipeline_v2(user_prompt: str, search_requests=None) -> dict:
    """
    Run the database-based recommendation pipeline.
    
    This pipeline:
    1. Uses Gemini AI to interpret the user's prompt into audio features & weights
    2. Searches the local parquet database using weighted Euclidean distance
    3. Returns the best matches from the database
    
    Args:
        user_prompt: User's playlist description
        search_requests: Not used in V2, included for consistent interface with V1
        
    Returns:
        dict with keys:
            - 'track_ids': list of Spotify track IDs
            - 'tracks': list of track details (id, name, artists, score)
            - 'targets': the AI-generated target feature values
            - 'weights': the AI-generated feature weights
            
    Raises:
        ValueError: If prompt is empty or search fails
        FileNotFoundError: If database file is missing
    """
    # Step 1: Get AI interpretation (uses LocalSearchParams schema - no seeds)
    ai_params_object = get_gemini_interpretation(user_prompt, LocalSearchParams)
    
    # Extract target features and weights as vectors
    targets, weights = ai_params_object.get_search_data()
    
    # Step 2: Search the local database
    search_engine = SearchEngine()
    db_recommendations = search_engine.search_db(
        target_vector=targets,
        weights_vector=weights,
        top_n=DEFAULT_PLAYLIST_LENGTH
    )
    
    if not db_recommendations:
        raise ValueError("Database search returned no results.")
    
    # Step 3: Extract track IDs for playlist creation
    track_ids = [track['track_id'] for track in db_recommendations]
    
    return {
        "track_ids": track_ids,
        "tracks": db_recommendations,  # Full track info (name, artist, score)
        "targets": targets,
        "weights": weights,
        "pipeline": "V2 (Database)"
    }
