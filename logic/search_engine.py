import os
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
from config.model_consts import FEATURE_ORDER

# Constants for Normalization
MAX_TEMPO = 250.0 
MAX_POPULARITY = 100.0

class LocalSearchEngine:
    """
    Logic for searching and ranking songs based on mathematical distance.
    Handles both Pipeline 1 (Simple API Params) and Pipeline 2 (Weighted Features).
    """

    def __init__(self):
        self.features_matrix = None
        self.meta_df = None
        self._is_loaded = False

    def _load_data_if_needed(self):
        if self._is_loaded:
            return

        print("DEBUG: Loading local dataset...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        npy_path = os.path.join(base_dir, 'songs_DB', 'songs_data.npy')
        meta_path = os.path.join(base_dir, 'songs_DB', 'songs_meta.csv')

        if os.path.exists(npy_path) and os.path.exists(meta_path):
            try:
                self.features_matrix = np.load(npy_path)
                self.meta_df = pd.read_csv(meta_path)
                self._is_loaded = True
            except Exception as e:
                print(f"ERROR: Failed to load local DB: {e}")
        else:
            print(f"ERROR: DB files not found.")

    def search_local(self, target_vector: np.array, weights_vector: np.array, top_n: int = 20) -> pd.DataFrame:
        """
        [Pipeline 2 Only] Search the local 170k song database.
        """
        self._load_data_if_needed()
        if self.features_matrix is None:
            return pd.DataFrame()

        # Math: Weighted Distance
        diff = self.features_matrix - target_vector
        squared_diff = diff ** 2
        weighted_squared_diff = weights_vector * squared_diff
        distances = np.sqrt(np.sum(weighted_squared_diff, axis=1))
        
        # Sort
        sorted_indices = np.argsort(distances)[:top_n]
        results = self.meta_df.iloc[sorted_indices].copy()
        results['score'] = distances[sorted_indices]
        
        return results

    @staticmethod
    def rank_remote_tracks(tracks: List[Dict], target_vector: np.array, weights_vector: np.array) -> List[Dict]:
        if not tracks:
            return []

        ranked_tracks = []

        for track in tracks:
            # Normalize tracks to 0-1 range to match our target vector
            current_features = [
                track.get('danceability', 0),
                track.get('energy', 0),
                track.get('valence', 0),
                track.get('speechiness', 0),
                track.get('acousticness', 0),
                track.get('instrumentalness', 0),
                track.get('tempo', 0) / MAX_TEMPO,
                track.get('popularity', 0) / MAX_POPULARITY
            ]
            
            track_vec = np.clip(current_features, 0.0, 1.0)
            
            # Math: Weighted Distance
            # If weight is 0 (Pipeline 1 'None' fields), that difference is ignored.
            diff = track_vec - target_vector
            dist = np.sqrt(np.sum(weights_vector * (diff ** 2)))
            
            track['match_score'] = float(dist) 
            ranked_tracks.append(track)

        ranked_tracks.sort(key=lambda x: x['match_score'])
        return ranked_tracks

    # ==========================================
    # CONVERTERS
    # ==========================================

    @staticmethod
    def convert_v1_to_vectors(v1_params) -> Tuple[np.array, np.array]:
        """
        [Pipeline 1 Converter]
        Converts simple 'AIRecommendationParams' to vectors.
        
        How it works:
        - Creates a 'Mask' vector: 1.0 if feature exists, 0.0 if None.
        - This ensures we don't penalize songs for features the user didn't specify.
        """
        target_list = []
        mask_list = [] # Acts as a binary weight vector

        for feature_name in FEATURE_ORDER:
            val = getattr(v1_params, feature_name, None)
            
            if val is not None:
                # Feature is active -> Mask = 1.0
                mask_list.append(1.0)
                
                # Normalize values
                if feature_name == 'tempo':
                    target_list.append(val / MAX_TEMPO)
                elif feature_name == 'popularity':
                    target_list.append(val / MAX_POPULARITY)
                else:
                    target_list.append(val)
            else:
                # Feature is inactive (None) -> Mask = 0.0
                mask_list.append(0.0)
                target_list.append(0.0) # Value doesn't matter because mask is 0

        return np.array(target_list), np.array(mask_list)

    @staticmethod
    def convert_v2_to_vectors(v2_params) -> Tuple[np.array, np.array]:
        """
        [Pipeline 2 Converter]
        Converts complex 'LocalSearchQueryParams' (with explicit weights) to vectors.
        """
        target_list = []
        weight_list = []

        for feature_name in FEATURE_ORDER:
            # Access nested object (e.g., params.energy.value)
            feature_obj = getattr(v2_params, feature_name, None)
            
            if feature_obj:
                target_list.append(feature_obj.value)
                weight_list.append(feature_obj.weight)
            else:
                target_list.append(0.5)
                weight_list.append(0.0)

        return np.array(target_list), np.array(weight_list)