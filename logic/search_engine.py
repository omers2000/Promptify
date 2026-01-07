import pandas as pd
import numpy as np
import os
from typing import List, Dict
from config.model_consts import FEATURE_ORDER, DEFAULT_PLAYLIST_LENGTH

class SearchEngine:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(current_dir)

        # The only path we need now
        self.db_path = os.path.join(self.project_root, 'songs_DB', 'tracks_db.parquet')

        self.features_matrix = None
        self.metadata_df = None
        self._is_loaded = False

    def load_data(self):
        if self._is_loaded:
            return

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}. Please run preprocess.py first.")

        print("Loading Unified Parquet Database...")
        meta_cols = ['track_id', 'track_name', 'artists']
        required_cols = meta_cols + FEATURE_ORDER
        full_df = pd.read_parquet(self.db_path, columns=required_cols)
        
        missing_features = [f for f in FEATURE_ORDER if f not in full_df.columns]
        if missing_features:
            raise ValueError(
                f"Database out of sync! Missing features: {missing_features}. "
                "Please run preprocess.py to rebuild the database."
            )

        # Feature matrix for calculations
        self.features_matrix = full_df[FEATURE_ORDER].to_numpy(dtype=np.float32)
    
        # Metadata for display
        self.metadata_df = full_df[meta_cols].copy()
    
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
    def _calculate_weighted_distance(candidates_matrix: np.ndarray, target_arr: np.ndarray, weights_arr: np.ndarray) -> np.ndarray:
        """
        Core Algorithm: Weighted Euclidean Distance.
        Math: Sum( weight_i * (candidate_i - target_i)^2 )
        Returns: A 1D array of scores (Lower score = Better match).
        """
        diff = candidates_matrix - target_arr
        squared_diff = diff ** 2
        weighted_diff = squared_diff * weights_arr
        return weighted_diff.sum(axis=1)


    @staticmethod
    def rank_reccobeats_candidates(candidates_list: List[Dict], target_vector: List[float], weights_vector: List[float]) -> List[Dict]:
        """
        Ranks tracks from ReccoBeats based on feature similarity.
        
        Args:
            candidates_list: List of track dictionaries containing metadata and raw audio features (from ReccoBeats).
            target_vector: The desired audio feature values to match against (from gemini/ReccoBeatsParams).
            weights_vector: Importance multipliers for each feature (0.0 to 1.0) (from gemini/ReccoBeatsParams).
            
        Returns:
            A list of track dictionaries, sorted by 'match_score_squared' (lowest is best),
            with the popularity weight forced to 0.0 as ReccoBeats lacks this data.
        """
        if not candidates_list:
            return []
        
        # --- 1. Handle Weights (Ignore Popularity for External API) ---
        weights_arr = np.array(weights_vector, dtype=np.float32)
        try:
            pop_idx = FEATURE_ORDER.index('popularity')
            weights_arr[pop_idx] = 0.0 # Force weight to 0 since API lacks this data
        except ValueError:
            pass

        # --- 2. Handle Target Vector Normalization ---
        norm_target = [
            SearchEngine._normalize_value(f, val) 
            for f, val in zip(FEATURE_ORDER, target_vector)
        ]
        target_arr = np.array(norm_target, dtype=np.float32)

        # --- 3. Extract AND Normalize Candidates ---
        candidates_matrix = []
        for track in candidates_list:
            row = []
            for f in FEATURE_ORDER:
                raw_val = track.get(f, 0.0)
                norm_val = SearchEngine._normalize_value(f, raw_val)
                row.append(norm_val)
            candidates_matrix.append(row)
            
        candidates_matrix = np.array(candidates_matrix, dtype=np.float32)
        scores = SearchEngine._calculate_weighted_distance(candidates_matrix, target_arr, weights_arr)

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
    
    def search_db(self, target_vector: List[float], weights_vector: List[float], top_n: int = DEFAULT_PLAYLIST_LENGTH) -> List[Dict]:
        """
        Searches the pre-processed local database for the most similar tracks.
        
        Args:
            target_vector: The normalized audio feature values to search for (from gemini/ReccoBeatsParams).
            weights_vector: Feature importance weights (from gemini/ReccoBeatsParams).
            top_n: Number of results to return (defults to DEFAULT_PLAYLIST_LENGTH if no value is given).
            
        Returns:
            A list of the top N closest matches from the local database,
            including metadata (ID, name, artists) and their calculated distance scores.
            
        Raises:
            FileNotFoundError: 
                If 'tracks_db.parquet' is missing. Occurs if preprocess.py was not run 
                or the database was moved.
            ValueError: 
                1. Feature Mismatch: If the Parquet file lacks columns defined in FEATURE_ORDER.
                2. Input Length Mismatch: If target_vector or weights_vector length 
                   does not exactly match len(FEATURE_ORDER).
            OSError: 
                If the Parquet file is corrupted, unreadable, or locked by another process.
        """
        if not self._is_loaded:
            self.load_data()
        
        expected_len = len(FEATURE_ORDER)
        if len(target_vector) != expected_len or len(weights_vector) != expected_len:
            raise ValueError(
                f"Input vector length mismatch. Expected {expected_len} features, "
                f"but got target({len(target_vector)}) and weights({len(weights_vector)})."
            )

        norm_target = [
            SearchEngine._normalize_value(f, val) 
            for f, val in zip(FEATURE_ORDER, target_vector)
        ]
        target_arr = np.array(norm_target, dtype=np.float32)
        weights_arr = np.array(weights_vector, dtype=np.float32)
        scores = self._calculate_weighted_distance(self.features_matrix, target_arr, weights_arr)

        num_songs = len(scores)
        if top_n >= num_songs:
            top_indices_sorted = np.argsort(scores)
        else:
            # Optimization: Use argpartition to find top N without full sort
            top_indices = np.argpartition(scores, top_n)[:top_n]
            top_indices_sorted = top_indices[np.argsort(scores[top_indices])]

        results = []
        for idx in top_indices_sorted:
            # Since they came from the same Parquet file, idx is guaranteed to match
            row = self.metadata_df.iloc[idx]
            results.append({
                'track_id': row['track_id'],
                'track_name': row['track_name'],
                'artists': row['artists'],
                'score_squared': float(scores[idx])
            })

        return results