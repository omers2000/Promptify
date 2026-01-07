import unittest
import numpy as np
import pandas as pd
from typing import List, Dict

# Adjust path to import logic from parent directory
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from logic.search_engine import SearchEngine
from config.model_consts import FEATURE_ORDER

class TestPipeline1_ExternalRanking(unittest.TestCase):
    """
    Tests for Pipeline 1: 'rank_reccobeats_candidates'.
    This method is static and Re-Ranks a small list of results from an API.
    """

    def setUp(self):
        # Define a standard order for readability in tests
        # ['acousticness', 'danceability', 'energy', 'tempo', 'valence', 'popularity']
        self.feature_order = FEATURE_ORDER

    def test_empty_candidate_list(self):
        """
        Edge Case: If the API returns no songs, the function should return an empty list
        without crashing.
        """
        result = SearchEngine.rank_reccobeats_candidates([], [0.5]*6, [1.0]*6)
        self.assertEqual(result, [])

    def test_perfect_match_score(self):
        """
        Functionality: If a candidate matches the target EXACTLY, the score should be 0.0.
        """
        # Target: 125 BPM (0.5 normalized), others 0.5
        target_vector = [0.5, 0.5, 0.5, 125, 0.5, 50] 
        weights_vector = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        # Candidate identical to target (Remember: engine normalizes raw inputs)
        candidate = {
            'id': '1', 
            'acousticness': 0.5, 'danceability': 0.5, 'energy': 0.5, 
            'tempo': 125, 'valence': 0.5, 'popularity': 50
        }

        results = SearchEngine.rank_reccobeats_candidates([candidate], target_vector, weights_vector)
        
        # Score should be effectively 0
        self.assertAlmostEqual(results[0]['match_score_squared'], 0.0, places=5)

    def test_tempo_normalization_logic(self):
        """
        Functionality: Ensure the engine correctly interprets raw BPM vs Normalized BPM.
        Target: 250 BPM. Candidate: 250 BPM.
        If normalization fails, 250 - 1.0 is a huge distance.
        If normalization works, 1.0 - 1.0 is 0 distance.
        """
        target_vector = [0, 0, 0, 250, 0, 0] # 250 BPM -> 1.0 normalized
        weights = [0, 0, 0, 1, 0, 0]         # Only care about Tempo

        candidate = {'id': 'fast', 'tempo': 250, 'acousticness': 0} 

        results = SearchEngine.rank_reccobeats_candidates([candidate], target_vector, weights)
        self.assertAlmostEqual(results[0]['match_score_squared'], 0.0, places=5)

    def test_popularity_is_ignored_in_pipeline1(self):
        """
        Functionality: Pipeline 1 (ReccoBeats API) usually does not return Popularity.
        The engine MUST forcefully set popularity weight to 0 internally to avoid skewing results.
        """
        target_vector = [0, 0, 0, 100, 0, 100] # User wants popular songs (100)
        
        # User emphasizes popularity heavily (Weight 10.0)
        weights_vector = [0, 0, 0, 0, 0, 10.0] 

        # Candidate has NO popularity field (defaults to 0 internally)
        candidate = {'id': 'A', 'tempo': 100} 

        results = SearchEngine.rank_reccobeats_candidates([candidate], target_vector, weights_vector)
        
        # If popularity weight was active: (0 - 1.0)^2 * 10 = 10.0 score.
        # If popularity weight was forced to 0: Score should be 0.0.
        self.assertAlmostEqual(results[0]['match_score_squared'], 0.0, places=5)

    def test_ranking_order(self):
        """
        Functionality: Ensure the list is actually sorted (Best match first).
        """
        target = [0.5, 0.5, 0.5, 125, 0.5, 50]
        weights = [1, 1, 1, 1, 1, 1]

        # Candidate A: Perfect match
        cand_a = {'id': 'perfect', 'acousticness': 0.5, 'tempo': 125, 'popularity': 50, 'energy': 0.5, 'danceability': 0.5, 'valence': 0.5}
        # Candidate B: Terrible match (Tempo 0 vs 125)
        cand_b = {'id': 'bad', 'acousticness': 0.5, 'tempo': 0, 'popularity': 50, 'energy': 0.5, 'danceability': 0.5, 'valence': 0.5}

        # Pass in wrong order
        results = SearchEngine.rank_reccobeats_candidates([cand_b, cand_a], target, weights)

        # Check if sorted correctly
        self.assertEqual(results[0]['id'], 'perfect')
        self.assertEqual(results[1]['id'], 'bad')


class TestPipeline2_LocalSearch(unittest.TestCase):
    """
    Tests for Pipeline 2: 'search_db'.
    This involves searching a large database using vectorized operations.
    We mock the database here to avoid loading the real 200MB file.
    """

    def setUp(self):
        # 1. Initialize Engine
        self.engine = SearchEngine()

        # 2. Mock the Data (Inject Fake DB)
        # We create a tiny DB with 3 distinct songs
        
        # Song 1: Quiet & Slow (Acoustic=1, Tempo=0 -> 0.0)
        # Song 2: Fast & Energetic (Energy=1, Tempo=250 -> 1.0)
        # Song 3: Balanced (All 0.5)
        
        # Note: The Mock DB is ALREADY NORMALIZED (simulating the .npy file)
        self.mock_features = np.array([
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0], # Song 1
            [0.0, 1.0, 1.0, 1.0, 1.0, 0.5], # Song 2
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # Song 3
        ], dtype=np.float32)

        self.mock_metadata = pd.DataFrame([
            {'track_id': 'id_1', 'track_name': 'Slow Song', 'artists': 'Artist A'},
            {'track_id': 'id_2', 'track_name': 'Party Song', 'artists': 'Artist B'},
            {'track_id': 'id_3', 'track_name': 'Mid Song', 'artists': 'Artist C'},
        ])

        # Inject into engine and bypass load_data()
        self.engine.features_matrix = self.mock_features
        self.engine.metadata_df = self.mock_metadata
        self.engine._is_loaded = True

    def test_find_nearest_neighbor(self):
        """
        Functionality: If I search for high energy and high tempo, 
        it should return 'Party Song' (Song 2) as the top result.
        """
        # Target: High Energy (1.0), High Tempo (250 BPM), others ignored
        target_vector = [0, 0, 1.0, 250, 0, 0] 
        weights =       [0, 0, 1.0, 1.0, 0, 0] # Only care about Energy & Tempo

        results = self.engine.search_db(target_vector, weights, top_n=1)
        
        self.assertEqual(results[0]['track_name'], 'Party Song')
        self.assertAlmostEqual(results[0]['score_squared'], 0.0, places=5)

    def test_target_normalization_in_local_search(self):
        """
        Functionality: The user sends raw Tempo (e.g., 125). 
        The DB is normalized (0-1). The engine MUST normalize the target 
        before calculating distance, otherwise distances will be huge.
        """
        # Target: Tempo 125 (should become 0.5 internally). 
        # Song 3 has Tempo 0.5. This should be a perfect match.
        target_vector = [0.5, 0.5, 0.5, 125, 0.5, 50] 
        weights = [1, 1, 1, 1, 1, 1]

        results = self.engine.search_db(target_vector, weights, top_n=1)

        self.assertEqual(results[0]['track_name'], 'Mid Song')
        # If normalization was missed, |125 - 0.5|^2 is huge. 
        # If correct, |0.5 - 0.5|^2 is 0.
        self.assertAlmostEqual(results[0]['score_squared'], 0.0, places=5)

    def test_top_n_larger_than_db(self):
        """
        Edge Case: User asks for 10 results, but DB only has 3 songs.
        Should return 3 results without crashing.
        """
        target = [0.5]*6
        weights = [1]*6

        results = self.engine.search_db(target, weights, top_n=10)
        self.assertEqual(len(results), 3)

    def test_zero_weights(self):
        """
        Edge Case: If weights are all zero, score should be zero for everyone 
        (all songs are equally 'perfect').
        """
        target = [0.0]*6
        weights = [0.0]*6 # User cares about nothing

        results = self.engine.search_db(target, weights, top_n=3)

        for res in results:
            self.assertAlmostEqual(res['score_squared'], 0.0, places=5)

if __name__ == '__main__':
    unittest.main()