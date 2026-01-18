"""
Pipeline V1: API-based recommendations using ReccoBeats API
Extracted from v1.py for use in the Streamlit app.
"""

from data_class.recommendation_params import ReccoBeatsParams
from rb.rb_functions import get_recommendations_ids_by_params, get_audio_features
from pipelines.search_engine import SearchEngine
from config.model_consts import DEFAULT_PLAYLIST_LENGTH
from pipelines.shared import get_gemini_interpretation


def _get_top_songs(ai_params_object, rec_track_ids: list, top_n: int) -> list:
    """Rank and return the top N track IDs from recommendations."""
    target_vector, weights_vector = ai_params_object.get_search_data()
    candidates_list = get_audio_features(rec_track_ids)
    sorted_songs = SearchEngine.rank_reccobeats_candidates(
        candidates_list, target_vector, weights_vector
    )
    return [song["spot_id"] for song in sorted_songs[:top_n]]


def run_pipeline_v1(user_prompt: str, search_requests) -> dict:
    """
    Run the API-based recommendation pipeline.
    
    This pipeline:
    1. Uses Gemini AI to interpret the user's prompt into audio features
    2. Finds seed songs on Spotify matching the AI's suggestions
    3. Calls ReccoBeats API to get recommendations based on seeds + features
    4. Ranks results using cosine similarity to target features
    
    Args:
        user_prompt: User's playlist description
        search_requests: Authenticated SearchRequests instance from Spotify
        
    Returns:
        dict with keys:
            - 'track_ids': list of recommended Spotify track IDs
            - 'seed_ids': list of seed track IDs that were used
            - 'params': the AI-generated parameters (for debugging/display)
            
    Raises:
        ValueError: If prompt is empty, no valid seeds found, or API returns nothing
    """
    # Step 1: Get AI interpretation of the prompt
    ai_params_object = get_gemini_interpretation(user_prompt, ReccoBeatsParams)
    
    params = ai_params_object.to_query_params()
    seeds = params.get("seeds", [])
    
    # Step 2: Resolve seed songs on Spotify
    valid_seed_ids = []
    resolved_seeds = []  # For display purposes
    
    for seed in seeds:
        track_name = seed.get('track_name')
        artist_name = seed.get('artist_name')
        seed_id = search_requests.get_id_by_song(track_name, artist_name)
        
        if seed_id:
            valid_seed_ids.append(seed_id)
            resolved_seeds.append({
                "track_name": track_name,
                "artist_name": artist_name,
                "spotify_id": seed_id
            })
    
    if not valid_seed_ids:
        raise ValueError(
            "Could not find any of the AI-suggested seed songs on Spotify. "
            "Try a different prompt."
        )
    
    # Step 3: Get recommendations from ReccoBeats API
    params['seeds'] = ",".join(valid_seed_ids)
    rec_track_ids = get_recommendations_ids_by_params(params)
    
    if not rec_track_ids:
        raise ValueError("ReccoBeats API returned no recommendations.")
    
    # Step 4: Rank and get top songs
    top_track_ids = _get_top_songs(
        ai_params_object, 
        rec_track_ids, 
        top_n=DEFAULT_PLAYLIST_LENGTH
    )
    
    return {
        "track_ids": top_track_ids,
        "seed_ids": valid_seed_ids,
        "resolved_seeds": resolved_seeds,
        "params": params,
        "pipeline": "V1 (API)"
    }
