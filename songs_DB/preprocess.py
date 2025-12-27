import pandas as pd
import numpy as np


def main():
    # Load the dataset
    df = pd.read_csv('dataset.csv')

    # Display basic information about the dataset
    print("Dataset Info:")
    print(df.info())

    # Check for missing values
    print("\nMissing Values:")
    print(df.isnull().sum())

    # Drop duplicates
    df = df.drop_duplicates().reset_index(drop=True)

    # Drop missing values in critical columns (remove NaNs and empty/whitespace-only strings)
    df = df.dropna(subset=['artists', 'track_name', 'track_id'])
    mask = (
        df['artists'].astype(str).str.strip().ne('') &
        df['track_name'].astype(str).str.strip().ne('')
    )
    df = df.loc[mask].copy()

    # Convert the df to numpy ndarray for processing
    data_array = df.to_numpy()
    np.save('songs_data.npy', data_array)
    print(f"Converted to NumPy array and saved to 'songs_data.npy' with shape {data_array.shape}")

    # Save column names (meta) as header-only CSV
    pd.DataFrame(columns=df.columns).to_csv('songs_meta.csv', index=False)
    print("Saved column names to 'songs_meta.csv'")

if __name__ == "__main__":
    main()
