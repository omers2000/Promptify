import pandas as pd
import numpy as np
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config.model_consts import FEATURE_ORDER # CRITICAL: This order must match EXACTLY with your Pydantic model later.

# ==========================================
# CONFIGURATION
# ==========================================

# The source file from Kaggle
INPUT_FILE = 'dataset.csv'

# Output files
OUTPUT_NPY = 'tracks_features.npy'  # Numerical matrix for the algorithm
OUTPUT_META = 'tracks_meta.csv'     # Metadata to display to the user

def normalize_column(df, col_name):
    if col_name == 'tempo':
        return df[col_name].clip(0, 250) / 250.0
        
    elif col_name == 'popularity':
        return df[col_name].clip(0, 100) / 100.0

    return df[col_name].clip(0, 1)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found in the current directory.")
        return

    print("Loading raw dataset...")
    df = pd.read_csv(INPUT_FILE)
    original_count = len(df)
    
    print("Cleaning data...")
    df = df.dropna(subset=['track_name', 'artists', 'track_id'] + FEATURE_ORDER)
    df = df.drop_duplicates(subset=['track_id'])
    
    df = df[(df['duration_ms'] >= 60000) & (df['duration_ms'] <= 900000)]
    df = df[df['tempo'] > 0]
    
    # CRITICAL: Reset index to ensure 0-based sequential indexing.
    # This guarantees that Row 5 in the .npy file corresponds to Row 5 in the .csv file.
    df = df.reset_index(drop=True)
    print(f"Data cleaned. {len(df)} tracks remaining (dropped {original_count - len(df)} rows).")

    print("Normalizing features...")
    features_df = pd.DataFrame()

    for feature in FEATURE_ORDER:
        features_df[feature] = normalize_column(df, feature)
        print(f"Normalized {feature}...")

    features_scaled = features_df.to_numpy(dtype=np.float32)
    
    np.save(OUTPUT_NPY, features_scaled)
    print(f"Saved normalized features to '{OUTPUT_NPY}' with shape {features_scaled.shape}")
    
    # Save the metadata (The UI Data)
    meta_columns = ['track_id', 'track_name', 'artists', 'album_name', 'track_genre']
    df[meta_columns].to_csv(OUTPUT_META, index=False)
    print(f"Saved metadata to '{OUTPUT_META}'")
    
    print("\n✅ PREPROCESS COMPLETE.")
    print("NOTE: When building the Search Engine, ensure you use this exact feature order:")
    print(FEATURE_ORDER)

if __name__ == "__main__":
    main()