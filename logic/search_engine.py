import pandas as pd
import numpy as np
import os
from typing import List, Dict
from config.model_consts import FEATURE_ORDER, DEFAULT_PLAYLIST_LENGTH

class SearchEngine:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        self.features_path = os.path.join(project_root, 'songs_DB', 'tracks_features.npy')
        self.meta_path = os.path.join(project_root, 'songs_DB', 'tracks_meta.csv')

        self.features_matrix = None
        self.metadata_df = None
        self._is_loaded = False

    def load_data(self):
        if self._is_loaded:
            return

        if not os.path.exists(self.features_path) or not os.path.exists(self.meta_path):
            raise FileNotFoundError(f"Database files not found in songs_DB/. Please run preprocess.py first.")

        print("Loading Local Database into Memory...")
        self.features_matrix = np.load(self.features_path)
        self.metadata_df = pd.read_csv(self.meta_path)
        self._is_loaded = True
        print(f"Database Loaded: {self.features_matrix.shape[0]} songs ready.")

    # ==========================================
    # STATIC MATH FUNCTIONS
    # ==========================================

    @staticmethod
    def _normalize_value(feature_name: str, value: float) -> float:
        if value is None:
            return 0.0
        
        non_negative_value = max(float(value), 0.0)
            
        if feature_name == 'tempo':
            return min(non_negative_value / 250.0, 1.0)
        elif feature_name == 'popularity':
            return min(non_negative_value / 100.0, 1.0)
        
        return min(non_negative_value, 1.0)
    
    @staticmethod
    def _calculate_weighted_distance(candidates_matrix: np.ndarray, target_vector: List[float], weights_vector: List[float]) -> np.ndarray:
        """
        Core Algorithm: Weighted Euclidean Distance.
        Math: Sum( weight_i * (candidate_i - target_i)^2 )
        Returns: A 1D array of scores (Lower score = Better match).
        """

        target_arr = np.array(target_vector)   
        weights_arr = np.array(weights_vector) 

        diff = candidates_matrix - target_arr
        squared_diff = diff ** 2
        weighted_diff = squared_diff * weights_arr
        scores = weighted_diff.sum(axis=1)

        return scores

    @staticmethod
    def rank_external_candidates(candidates_list: List[Dict[str, float]], target_vector: List[float], weights_vector: List[float]) -> List[Dict]:
        if not candidates_list:
            return []
        
        # --- 1. Handle Weights (Ignore Popularity for External API) ---
        local_weights = np.array(weights_vector)
        try:
            pop_idx = FEATURE_ORDER.index('popularity')
            local_weights[pop_idx] = 0.0 # Force weight to 0 since API lacks this data
        except ValueError:
            pass

        # --- 2. Handle Target Vector Normalization ---
        norm_target = [
            SearchEngine._normalize_value(f, val) 
            for f, val in zip(FEATURE_ORDER, target_vector)
        ]

        # --- 3. Extract AND Normalize Candidates ---
        candidates_matrix = []
        for track in candidates_list:
            row = []
            for f in FEATURE_ORDER:
                raw_val = track.get(f, 0.0)
                norm_val = SearchEngine._normalize_value(f, raw_val)
                row.append(norm_val)
            candidates_matrix.append(row)
            
        candidates_matrix = np.array(candidates_matrix)
        scores = SearchEngine._calculate_weighted_distance(candidates_matrix, norm_target, local_weights)

        ranked_results = []
        for i, track in enumerate(candidates_list):
            track_with_score = track.copy()
            track_with_score['match_score_squared'] = float(scores[i])
            ranked_results.append(track_with_score)

        ranked_results.sort(key=lambda x: x['match_score_squared'])

        return ranked_results

    # ==========================================
    # INSTANCE METHODS (Require Loaded DB)
    # ==========================================
    
    def search_local(self, target_vector: List[float], weights_vector: List[float], top_n: int = DEFAULT_PLAYLIST_LENGTH) -> List[Dict]:
        if not self._is_loaded:
            self.load_data()

        norm_target = [
            SearchEngine._normalize_value(f, val) 
            for f, val in zip(FEATURE_ORDER, target_vector)
        ]

        scores = self._calculate_weighted_distance(self.features_matrix, norm_target, weights_vector)

        num_songs = len(scores)
        if top_n >= num_songs:
            top_indices_sorted = np.argsort(scores)
        else:
            # Optimization: Use argpartition to find top N without full sort
            top_indices = np.argpartition(scores, top_n)[:top_n]
            top_indices_sorted = top_indices[np.argsort(scores[top_indices])]

        results = []
        for idx in top_indices_sorted:
            row = self.metadata_df.iloc[idx]
            results.append({
                'track_id': row['track_id'],
                'track_name': row['track_name'],
                'artists': row['artists'],
                'score_squared': float(scores[idx])
            })

        return results