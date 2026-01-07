import pandas as pd
import numpy as np
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config.model_consts import FEATURE_ORDER # CRITICAL: This order must match EXACTLY with your Pydantic model later.

# INVARIANT:
# Row i in self.features_matrix corresponds exactly to row i in self.metadata_df
# Both originate from the same Parquet row and must never be reordered independently.

# ==========================================
# CONFIGURATION
# ==========================================

INPUT_FILE = os.path.join(current_dir, 'dataset.csv')
OUTPUT_DB = os.path.join(current_dir, 'tracks_db.parquet')

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
    
    # Reset index to guarantee row alignment between metadata and features.
    # This preserves invariant: row i in features ↔ row i in metadata
    df = df.reset_index(drop=True)
    print(f"Data cleaned. {len(df)} tracks remaining (dropped {original_count - len(df)} rows).")

    print("Normalizing features...")
    features_df = pd.DataFrame()

    for feature in FEATURE_ORDER:
        features_df[feature] = normalize_column(df, feature).astype(np.float32)
        print(f"Normalized {feature}...")

    # --- NEW: UNIFIED STORAGE LOGIC ---
    print("Creating unified database...")
    meta_columns = ['track_id', 'track_name', 'artists', 'album_name', 'track_genre']
    
    # Combine metadata and normalized features into a single DataFrame
    final_db = pd.concat([df[meta_columns], features_df], axis=1)
    
    # Save as Parquet - this keeps everything perfectly aligned
    final_db.to_parquet(OUTPUT_DB, engine='pyarrow', index=False)
    
    print(f"✅ Saved unified database to '{OUTPUT_DB}' with shape {final_db.shape}")

if __name__ == "__main__":
    main()