import unittest
import pandas as pd
import numpy as np
import os
import sys

# Add the parent directory to sys.path to import config modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.model_consts import FEATURE_ORDER

class TestDatabaseSynchronization(unittest.TestCase):
    """
    Integration Test:
    Verifies that the generated .npy matrix and .csv metadata 
    are perfectly synchronized with the raw source dataset.
    """

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests. Loads the actual data files.
        """
        # Define paths relative to the project root
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.npy_path = os.path.join(cls.base_dir, 'songs_DB', 'tracks_features.npy')
        cls.meta_path = os.path.join(cls.base_dir, 'songs_DB', 'tracks_meta.csv')
        cls.raw_path = os.path.join(cls.base_dir, 'songs_DB', 'dataset.csv')

        # Check if files exist
        if not os.path.exists(cls.npy_path) or not os.path.exists(cls.meta_path):
            raise FileNotFoundError("Processed data files not found. Please run 'songs_DB/preprocess.py' first.")

        # Load data
        print(f"\n📂 Loading data for sync verification...")
        cls.matrix = np.load(cls.npy_path)
        cls.meta_df = pd.read_csv(cls.meta_path)
        cls.raw_df = pd.read_csv(cls.raw_path)

    def test_dimensions_match(self):
        """
        Test 1: Structural Integrity.
        Ensures that the number of rows in the matrix matches the number of rows in the metadata.
        """
        matrix_rows = self.matrix.shape[0]
        meta_rows = len(self.meta_df)
        
        print(f"   Checking dimensions: Matrix ({matrix_rows}) vs Metadata ({meta_rows})...")
        
        self.assertEqual(matrix_rows, meta_rows, 
                         "Mismatch between Matrix rows and Metadata rows! The index will be broken.")

    def test_feature_order_integrity(self):
        """
        Test 2: Data Value Synchronization.
        Picks a specific song (Index 0) and manually recalculates its normalized values
        from the raw CSV to ensure they match the matrix exactly.
        
        This prevents the 'Tempo vs Energy' swap error.
        """
        TEST_INDEX = 0
        
        # 1. Get the track ID from the metadata (The 'Index' used by the engine)
        track_id = self.meta_df.iloc[TEST_INDEX]['track_id']
        track_name = self.meta_df.iloc[TEST_INDEX]['track_name']
        
        print(f"\n   🎵 Verifying track at Index {TEST_INDEX}: '{track_name}' (ID: {track_id})")

        # 2. Find the corresponding raw row in the original CSV
        raw_row_matches = self.raw_df[self.raw_df['track_id'] == track_id]
        
        # Ensure the track exists in the raw DB
        self.assertGreater(len(raw_row_matches), 0, "Track from metadata not found in raw CSV!")
        
        raw_row = raw_row_matches.iloc[0]
        
        # 3. Get the vector from the processed matrix
        matrix_vector = self.matrix[TEST_INDEX]

        # 4. Iterate through the exact feature order used by the app
        for i, feature in enumerate(FEATURE_ORDER):
            
            # The value stored in the matrix (Engine data)
            actual_matrix_val = matrix_vector[i]
            
            # The raw value from the CSV
            raw_val = raw_row[feature]
            
            # Manually calculate expected normalization (Logic must match preprocess.py)
            expected_val = 0.0
            if feature == 'tempo':
                expected_val = min(raw_val, 250) / 250.0
            elif feature == 'popularity':
                expected_val = min(raw_val, 100) / 100.0
            else:
                expected_val = min(raw_val, 1.0)

            print(f"      Checking {feature:<15}: Raw={raw_val:<10} Expected={expected_val:.4f} Actual={actual_matrix_val:.4f}")

            # Assert equality with a small tolerance for floating point arithmetic
            self.assertAlmostEqual(
                actual_matrix_val, 
                expected_val, 
                places=4, 
                msg=f"Data Mismatch for feature '{feature}'! The columns might be mixed up."
            )

if __name__ == '__main__':
    unittest.main()