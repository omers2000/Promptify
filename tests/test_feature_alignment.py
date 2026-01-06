import unittest
import numpy as np
import sys
import os

# Add the parent directory path to allow importing our custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.model_consts import FEATURE_ORDER
from data_class.recommendation_params import LocalSearchParams, AudioFeatures, FeatureWeights
from logic.search_engine import SearchEngine

class TestFeatureAlignment(unittest.TestCase):
    
    def test_pipeline_integrity(self):
        """
        CRITICAL CHECK: Ensures that what goes into Pydantic comes out 
        in the EXACT same order the Engine expects (based on FEATURE_ORDER).
        """
        print(f"\n🔍 Testing Feature Alignment based on: {FEATURE_ORDER}")

        # 1. Generate unique but type-valid values to act as "ID cards" for each feature.
        unique_values = {}
        
        for i, feature in enumerate(FEATURE_ORDER):
            base_val = (i + 1)
            
            if feature == 'popularity':
                # Popularity must be an int (e.g., 60)
                unique_values[feature] = int(base_val * 10)
            elif feature == 'tempo':
                # Tempo can be a large float (e.g., 120.0)
                unique_values[feature] = float(base_val * 20)
            else:
                # All other features are floats between 0 and 1 (e.g., 0.1, 0.2)
                unique_values[feature] = float(base_val) / 10.0

        print(f"Generated Test Values: {unique_values}")

        # Create the Pydantic object
        params = LocalSearchParams(
            target_features=AudioFeatures(**unique_values),
            feature_weights=FeatureWeights() 
        )

        # 2. Convert to vector (The actual data structure sent to the Search Engine)
        target_vector, _ = params.get_search_data()

        # 3. Verify the vector is ordered exactly according to FEATURE_ORDER configuration
        print("\nChecking Vector vs Config Order:")
        for i, feature_name in enumerate(FEATURE_ORDER):
            expected_val = unique_values[feature_name]
            actual_val = target_vector[i]
            
            # Pydantic might convert int to float in the final list, which is expected behavior
            self.assertAlmostEqual(actual_val, float(expected_val), places=5, 
                                   msg=f"CRITICAL ERROR: Mismatch at {feature_name}! Pipeline order is broken.")
            
        print("✅ Pipeline Integrity Check Passed: Inputs matched Outputs perfectly.")

    def test_search_engine_calculation(self):
        """
        Mathematical Check: Does the engine calculate a distance of 0.0 
        when the query vector is identical to the song vector?
        """
        # Create a dummy vector of the correct length with unique values
        # We are not using Pydantic here, but injecting directly into the engine logic
        unique_vals = np.array([(i + 1) / 10.0 for i in range(len(FEATURE_ORDER))], dtype=np.float32)
        
        engine = SearchEngine()
        
        # Inject a single song into the engine's matrix that is exactly our vector
        engine.features_matrix = np.array([unique_vals], dtype=np.float32)
        
        # Use uniform weights
        weights = [1.0] * len(FEATURE_ORDER)
        
        # Direct distance calculation
        # Note: We send unique_vals as both the 'matrix' (song) and the 'target' (query)
        scores = engine._calculate_weighted_distance(
            engine.features_matrix, 
            unique_vals, 
            weights
        )
        
        print(f"\nMath Check: Distance score is {scores[0]}")
        
        # The distance must be zero
        self.assertAlmostEqual(scores[0], 0.0, places=5, 
                               msg="Engine calculated distance > 0 for identical vectors! Indices might be mixed up.")
        print("✅ Math Check Passed: Engine logic is aligned.")

if __name__ == '__main__':
    unittest.main()