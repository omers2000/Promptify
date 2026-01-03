import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# ==========================================
# CONFIGURATION
# ==========================================

# The source file from Kaggle
INPUT_FILE = 'dataset.csv'

# Output files
OUTPUT_NPY = 'tracks_features.npy'  # The "Brain": Numerical matrix for the algorithm
OUTPUT_META = 'tracks_meta.csv'     # The "Face": Metadata to display to the user

# CRITICAL: This order must match EXACTLY with your Pydantic model later.
# We removed 'loudness' as discussed, and kept 'speechiness' & 'instrumentalness'.
NUMERIC_FEATURES = [
    'danceability', 
    'energy', 
    'valence', 
    'speechiness', 
    'acousticness', 
    'instrumentalness', 
    'tempo',
    'popularity'
]

def main():
    # 1. Validation
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found in the current directory.")
        return

    print("Loading raw dataset...")
    df = pd.read_csv(INPUT_FILE)
    original_count = len(df)
    
    # ==========================================
    # 2. DATA CLEANING
    # ==========================================
    print("Cleaning data...")
    
    # Drop rows where essential information is missing
    # We need track_id for Spotify, and numeric features for the math.
    df = df.dropna(subset=['track_name', 'artists', 'track_id'] + NUMERIC_FEATURES)
    
    # Drop duplicate songs based on Spotify ID to avoid repetition in playlists
    df = df.drop_duplicates(subset=['track_id'])
    
    # Filter out logical outliers:
    # - Songs shorter than 1 minute (usually intros/noise)
    # - Songs longer than 15 minutes (to keep the playlist flow)
    # - Songs with 0 Tempo (invalid data)
    df = df[(df['duration_ms'] >= 60000) & (df['duration_ms'] <= 900000)]
    df = df[df['tempo'] > 0]
    
    # CRITICAL: Reset index to ensure 0-based sequential indexing.
    # This guarantees that Row 5 in the .npy file corresponds to Row 5 in the .csv file.
    df = df.reset_index(drop=True)
    
    print(f"Data cleaned. {len(df)} tracks remaining (dropped {original_count - len(df)} rows).")

    # ==========================================
    # 3. NORMALIZATION (MinMax Scaling)
    # ==========================================
    print("Normalizing features...")
    
    # Initialize the scaler
    # This transforms all values (like Tempo 120 or Energy 0.8) into a range of [0, 1].
    # Without this, 'tempo' would dominate the Euclidean distance calculation.
    scaler = MinMaxScaler()
    
    # Create the matrix (numpy array)
    features_scaled = scaler.fit_transform(df[NUMERIC_FEATURES])
    
    # ==========================================
    # 4. EXPORT
    # ==========================================
    
    # Save the numerical matrix (The Engine)
    np.save(OUTPUT_NPY, features_scaled)
    print(f"Saved normalized features to '{OUTPUT_NPY}' with shape {features_scaled.shape}")
    
    # Save the metadata (The UI Data)
    # We only keep columns relevant for display or API calls
    meta_columns = ['track_id', 'track_name', 'artists', 'album_name', 'track_genre']
    df[meta_columns].to_csv(OUTPUT_META, index=False)
    print(f"Saved metadata to '{OUTPUT_META}'")
    
    print("\n✅ PREPROCESS COMPLETE.")
    print("NOTE: When building the Search Engine, ensure you use this exact feature order:")
    print(NUMERIC_FEATURES)

if __name__ == "__main__":
    main()