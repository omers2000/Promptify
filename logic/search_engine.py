import pandas as pd
import numpy as np
import os
from typing import List, Dict, Any
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
        self.features_matrix = np.load(self.features_path).astype(np.float32)
        self.metadata_df = pd.read_csv(self.meta_path)

        if self.features_matrix.shape[0] != len(self.metadata_df):
            raise ValueError(
                f"CRITICAL SYNC ERROR: Database files do not match. "
                f"Features has {self.features_matrix.shape[0]} rows, "
                f"but Metadata has {len(self.metadata_df)} rows. "
                "Please delete files in songs_DB and run preprocess.py again."
            )
        
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
    def rank_reccobeats_candidates(candidates_list: List[Dict[str, Any]], target_vector: List[float], weights_vector: List[float]) -> List[Dict[str, Any]]:
        """
        Ranks tracks from ReccoBeats based on feature similarity.
        
        Args:
            candidates_list: List of track dictionaries containing metadata and raw audio features.
            target_vector: The desired audio feature values to match against.
            weights_vector: Importance multipliers for each feature (0.0 to 1.0).
            
        Returns:
            A list of track dictionaries, sorted by 'match_score_squared' (lowest is best),
            with the popularity weight forced to 0.0 as external APIs often lack this real-time data.
        """
        if not candidates_list:
            return []
        
        # --- 1. Handle Weights (Ignore Popularity for External API) ---
        local_weights = np.array(weights_vector, dtype=np.float32)
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
        scores = SearchEngine._calculate_weighted_distance(candidates_matrix, target_arr, local_weights)

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
            target_vector: The normalized audio feature values to search for.
            weights_vector: Feature importance weights.
            top_n: Number of results to return (defults to DEFAULT_PLAYLIST_LENGTH if no value is given).
            
        Returns:
            A list of the top N closest matches from the local CSV/NPY database,
            including metadata (ID, name, artists) and their calculated distance scores.
            
        Raises:
            FileNotFoundError: If the .npy or .csv database files are missing from the disk.
            ValueError: If the database files are out of sync (row count mismatch) or if 
                        input vector lengths do not match FEATURE_ORDER.
            OSError: If database files exist but cannot be read due to permissions or corruption.
        """
        if not self._is_loaded:
            self.load_data()

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
            row = self.metadata_df.iloc[idx]
            results.append({
                'track_id': row['track_id'],
                'track_name': row['track_name'],
                'artists': row['artists'],
                'score_squared': float(scores[idx])
            })

        return results