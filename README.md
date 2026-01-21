# Promptify: AI-Powered Playlist Generation 🎵
### **Authors: Daniel Laroz and Omer Shapira**

## Live Demo
[https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app](https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app)

---

## Table of Contents

1. [Introduction](#Introduction)
   - [Background and Motivation](#Background-and-Motivation)
   - [Project Goals](#Project-Goals)
   - [Research Question](#Research-Question)
     
2. [System Design](#System-Design)
    - [High-Level Architecture](#High-Level-Architecture)
    - [Technologies](#Technologies)
     
3. [Methods & Approaches](#Methods-&-Approaches)
    - [Prompt Engineering Challenge](#Prompt-Engineering-Challenge)
    - [Pipeline A: API-Based Recommendations (ReccoBeats)](#Pipeline-A-API-Based-Recommendations-(ReccoBeats))
    - [Pipeline B: Local Database Search](#Pipeline-B-Local-Database-Search)
    - [Search Algorithm: Weighted Euclidean Distance](#Search-Algorithm-Weighted-Euclidean-Distance)
    - [Data Preprocessing](#Data-Preprocessing)
   
4. [Experimental Setup](#Experimental-Setup)
    - [Methodology](#Methodology)
    - [Data Collection](#Data-Collection)
    - [Test Prompts](#Test-Prompts)

5. [Results](#Results)
   
6. [Implementation & Demo](#Implementation-&-Demo)
    - [User Interface](#User-Interface)
    - [Technical Challenges & Solutions](#Technical-Challenges-&-Solutions)

7. [Code Overview](#Code-Overview)
    - [Project Structure](#Project-Structure)
    - [Key Components](#Key-Components)
     
8. [Conclusions](#Conclusions)
    - [Preliminary Observations](#Preliminary-Observations)
    - [Limitations](#Limitations)
    - [Future Improvements](#Future-Improvements)

9. [Usage](#Usage)

10. [References](#References)

---

## Introduction

Promptify is a web-based music recommendation system that allows users to generate Spotify playlists using natural language descriptions. Instead of manually searching for songs, users can describe their desired mood or activity in plain English—such as "energetic workout music with heavy beats" or "calm acoustic songs for studying"—and receive personalized recommendations.

The system is designed around a comparative architecture: it utilizes two different recommendation pipelines to provide results. Users can then vote on which playlist better matches their intent, enabling a data-driven comparison of different recommendation approaches.

### Background and Motivation

Human musical desires are frequently expressed through abstract concepts involving atmosphere or vibes. However, standard search mechanisms often rely on specific artist names, track titles, or distinct genres. These traditional methods can struggle to interpret semantic nuances, making it difficult to map abstract descriptions to appropriate musical content.

### Project Goals

The objective of Promptify is to automate the translation of abstract user intent into a curated list of tracks. The solution utilizes the Natural Language Processing (NLP) capabilities of Google Gemini to analyze free-text prompts. The system distills this text into quantifiable audio parameters and features, which serve as the foundation for the search and retrieval process.

### Research Question

**Which approach yields better playlist recommendations: an API-based method that leverages external recommendation algorithms, or a local database search using weighted similarity metrics?**

Beyond the system implementation, this project focuses on a comparative study of these two algorithmic approaches, evaluating their effectiveness through gathered user feedback and runtime comparison.

---

## System Design

### High-Level Architecture

```mermaid
graph TD
    classDef startEnd fill:#f9f,stroke:#333,stroke-width:2px,color:#000;
    classDef process fill:#d4e1f5,stroke:#333,stroke-width:1px,color:#000;
    classDef decision fill:#ffe0b2,stroke:#e65100,stroke-width:2px,color:#000;
    classDef api fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000;

    User([User Prompt]):::startEnd --> Gemini[Gemini AI Interpretation]:::process
    Gemini --> Split{Pipeline Split}:::decision

    Split -- "Pipeline A: API-Based" --> A_Data[Seeds + Audio Features + Weights]:::process
    A_Data --> ReccoAPI[ReccoBeats API]:::api
    ReccoAPI --> A_Filter[Re-rank via Weighted Euclidean Distance]:::process
    A_Filter --> Merge(( ))

    Split -- "Pipeline B: Local DB" --> B_Data[Audio Features + Weights]:::process
    B_Data --> LocalDB[Weighted Euclidean Search in Parquet DB]:::process
    LocalDB --> Merge

    Merge --> Spotify[Spotify API: Create Playlists]:::api
    Spotify --> Vote([User Votes for Better Playlist]):::startEnd
```

### Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **LLM** | Google Gemini 2.5 Flash Lite | Structured JSON output, fast inference, cost-effective |
| **Backend** | Python | Rich ecosystem for data science and API integration |
| **Music Data API** | ReccoBeats API | Provides recommendation endpoints with audio feature filtering |
| **Music Integration** | Spotify Web API (Spotipy) | Industry standard, rich metadata, playlist creation |
| **Local Database** | Parquet (PyArrow) | Columnar storage, fast vectorized operations with NumPy |
| **Frontend** | Streamlit | Rapid prototyping, built-in state management, easy deployment |
| **Data Collection** | Google Sheets API (gspread) | Simple vote logging, real-time collaboration |

---

## Methods & Algorithms

### Prompt Engineering Challenge

The first challenge is translating a user's abstract natural language prompt into quantifiable audio features. We use Google Gemini with structured output (Pydantic schemas) to ensure consistent, parseable responses.

**Audio Features Used:**

| Feature | Range | Description |
|---------|-------|-------------|
| `acousticness` | 0.0 - 1.0 | Confidence measure of acoustic sound |
| `danceability` | 0.0 - 1.0 | Suitability for dancing based on tempo, rhythm stability, beat strength |
| `energy` | 0.0 - 1.0 | Perceptual measure of intensity and activity |
| `tempo` | 0 - 250 BPM | Estimated beats per minute |
| `valence` | 0.0 - 1.0 | Musical positiveness (0 = sad, 1 = happy) |
| `popularity` | 0 - 100 | Current popularity on Spotify |

**Weight System:**

For each feature, Gemini also assigns an importance weight (0.0 to 1.0):
- **1.0** = Critical constraint (must match closely)
- **0.0** = Irrelevant (ignore this feature)

This allows the system to understand that "upbeat workout music" should heavily weight `energy` and `tempo`, while "chill background music" should prioritize `acousticness` and low `energy`.

---

### Pipeline A: API-Based Recommendations (ReccoBeats)

**Description:** This pipeline leverages external algorithmic recommendations from the ReccoBeats API, then re-ranks the results locally using our similarity metric.

**Process:**

1. **Gemini Interpretation:** The user prompt is sent to Gemini with a schema that requires:
   - Target audio feature values
   - Feature weights
   - **5 seed songs** (track name + artist name)

2. **Seed Resolution:** The suggested seed songs are searched on Spotify to obtain their track IDs. Invalid or non-existent songs are filtered out.

3. **API Request:** The ReccoBeats API is called with:
   - Seed track IDs
   - Target audio feature values
   - Request for 40 candidate tracks

4. **Re-Ranking:** The 40 candidates are ranked using **Weighted Euclidean Distance** against the target features. The top 10 tracks are selected.

```python
# Core ranking algorithm (simplified)
def rank_candidates(candidates, target, weights):
    scores = []
    for track in candidates:
        distance = sum(w * (track[f] - target[f])**2 for f, w in zip(features, weights))
        scores.append((track, distance))
    return sorted(scores, key=lambda x: x[1])
```

**Advantages:**
- Leverages ReccoBeats' recommendation algorithm
- Can discover tracks outside our local database
- Seed songs guide the recommendation toward the user's intent

**Disadvantages:**
- Dependent on external API availability
- ReccoBeats may occasionally recommends Track IDs that are not found on Spotify
- ReccoBeats lacks the ability to set a hard filter on popularity
- Pipeline's respone time is slower

---

### Pipeline B: Local Database Search

**Description:** This pipeline performs a direct similarity search on a pre-processed local database of ~90,000 tracks using weighted Euclidean distance.

**Process:**

1. **Gemini Interpretation:** The user prompt is sent to Gemini with a simpler schema:
   - Target audio feature values
   - Feature weights
   - **No seed songs required**

2. **Database Search:** A NumPy operation calculates the weighted Euclidean distance between the target vector and all tracks in the database:

```python
# Core Algorithm: Weighted Euclidean Distance
diff = candidates_matrix - target_arr
squared_diff = diff ** 2
weighted_diff = squared_diff * weights_arr
scores = weighted_diff.sum(axis=1)  # Lower = Better match
```

3. **Result Selection:** The top 10 tracks with the lowest distance scores are selected.

**Advantages: (in recommendation phase)**
- No external API dependency
- Faster response times
- Full control over the ranking algorithm
- Consistent, reproducible results

**Disadvantages:**
- Limited to tracks in the local database
- Database requires periodic updates

---

### Search Algorithm: Weighted Euclidean Distance

Both pipelines use the same core similarity metric:

$$\text{Distance Squared} = \sum_{i=1}^{n} w_i \cdot (x_i - t_i)^2$$

Where:
- $x_i$ = candidate track's feature value (normalized to 0-1)
- $t_i$ = target feature value
- $w_i$ = feature weight (0.0 = ignore, 1.0 = critical)

Lower distance = better match.

---

### Data Preprocessing

The local database is built from a CSV dataset ([Spotify Tracks Dataset on Kaggle](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)) containing Spotify track metadata and audio features. The preprocessing pipeline (`songs_DB/preprocess.py`) transforms this raw data into an optimized format for fast similarity searches.

#### Step 1: Data Cleaning

The raw dataset undergoes several cleaning operations to ensure data quality:

```python
# Remove rows with missing values in critical columns
df = df.dropna(subset=['track_name', 'artists', 'track_id'] + FEATURE_ORDER)

# Remove duplicate tracks (based on track_id)
df = df.drop_duplicates(subset=['track_id'])

# Filter out tracks with invalid durations
df = df[(df['duration_ms'] >= 60000) & (df['duration_ms'] <= 900000)]  # 1-15 minutes

# Filter out tracks with invalid tempo
df = df[df['tempo'] > 0]
```

**Cleaning Rationale:**
- **Duration filtering (1-15 min):** Excludes intros, interludes, and abnormally long tracks that don't represent typical songs
- **Tempo validation:** Removes corrupted entries where BPM detection failed
- **Deduplication:** Ensures each track appears exactly once in the database

#### Step 2: Feature Normalization

All audio features are normalized to a 0-1 range to ensure equal contribution during distance calculations:

| Feature | Original Range | Normalization Method |
|---------|----------------|---------------------|
| `tempo` | 0-250+ BPM | `clip(0, 250) / 250` |
| `popularity` | 0-100 | `clip(0, 100) / 100` |
| `acousticness` | 0.0-1.0 | `clip(0, 1)` (already normalized) |
| `danceability` | 0.0-1.0 | `clip(0, 1)` (already normalized) |
| `energy` | 0.0-1.0 | `clip(0, 1)` (already normalized) |
| `valence` | 0.0-1.0 | `clip(0, 1)` (already normalized) |

```python
def normalize_column(df, col_name):
    if col_name == 'tempo':
        return df[col_name].clip(0, 250) / 250.0
    elif col_name == 'popularity':
        return df[col_name].clip(0, 100) / 100.0
    return df[col_name].clip(0, 1)  # Safety clamp for already-normalized features
```

#### Step 3: Feature Ordering Invariant

A critical design constraint is the **strict feature ordering** defined in `config/model_consts.py`:

```python
FEATURE_ORDER = [
    'acousticness',
    'danceability', 
    'energy', 
    'tempo',
    'valence',  
    'popularity'
]
```

This ordering is enforced across the entire codebase:
- **Preprocessing:** Features are stored in this exact order
- **Gemini Output:** Pydantic schemas output values in this order
- **Search Engine:** NumPy arrays expect this column order

**Why this matters:** The weighted Euclidean distance calculation uses vectorized NumPy operations where feature positions must match between the target vector (from Gemini) and the database matrix.

#### Step 4: Unified Storage

The final database combines metadata and normalized features into a single Parquet file:

```python
# Metadata columns preserved for display
meta_columns = ['track_id', 'track_name', 'artists', 'album_name', 'track_genre']

# Combine metadata + normalized features
final_db = pd.concat([df[meta_columns], features_df], axis=1)

# Save as Parquet for efficient columnar access
final_db.to_parquet('tracks_db.parquet', engine='pyarrow', index=False)
```

**Storage Format Benefits:**
- **Parquet columnar format:** Enables fast loading of only the feature columns needed for search
- **PyArrow engine:** Provides efficient memory mapping and vectorized operations
- **Single file:** Maintains row alignment invariant between metadata and features

**Database Statistics:**
- Final size: ~90,000 tracks after cleaning
- File format: Apache Parquet
- Feature precision: float32 (memory-efficient while preserving accuracy)

---

## Experimental Setup

### Methodology

We designed an A/B testing framework where users generate playlists using both pipelines simultaneously and vote for which one better matches their prompt.

**Voting Options:**
- **Option A is Better** (Pipeline A wins)
- **Option B is Better** (Pipeline B wins)
- **It's a Tie** (Both equally good)

**Important:** Users are **not told** which pipeline corresponds to which option.

### Data Collection

Each vote records:
- Timestamp
- User's original prompt
- Vote result (V1 / V2 / Tie)
- Number of tracks in each playlist
- Voter's Spotify display name
- Runtime of each pipeline (seconds)

All data is logged to a Google Sheet for analysis.

### Test Prompts

We encouraged users to test diverse prompt types:

| Category | Example Prompts |
|----------|-----------------|
| Mood-based | "Melancholic songs for a rainy evening" |
| Activity-based | "High-energy workout music" |
| Genre-specific | "90s hip-hop classics" |
| Scenario-based | "Background music for a dinner party" |
| Abstract/Poetic | "Songs that feel like a sunset at the beach" |

---

## Results

### Voting Data

<!-- DATA_PLACEHOLDER_START -->
*Results will be populated from Google Sheets data.*

| Metric | Value |
|--------|-------|
| Total Votes | TBD |
| Pipeline A Wins | TBD |
| Pipeline B Wins | TBD |
| Ties | TBD |

<!-- DATA_PLACEHOLDER_END -->

### Performance Comparison

<!-- PERFORMANCE_PLACEHOLDER_START -->
*Performance metrics will be populated from Google Sheets data.*

| Metric | Pipeline A (API) | Pipeline B (Local) |
|--------|------------------|-------------------|
| Average Runtime | TBD | TBD |
| Success Rate | TBD | TBD |

<!-- PERFORMANCE_PLACEHOLDER_END -->

### Analysis by Prompt Type

<!-- ANALYSIS_PLACEHOLDER_START -->
*Detailed analysis will be added based on collected data.*

| Prompt Category | Pipeline A Wins | Pipeline B Wins | Ties |
|-----------------|-----------------|-----------------|------|
| Mood-based | TBD | TBD | TBD |
| Activity-based | TBD | TBD | TBD |
| Genre-specific | TBD | TBD | TBD |
| Scenario-based | TBD | TBD | TBD |

<!-- ANALYSIS_PLACEHOLDER_END -->

---

## Implementation & Demo

### User Interface

The Streamlit application provides a clean, intuitive interface:

**1. Login Screen**

Users authenticate with their Spotify account via OAuth 2.0 to enable playlist creation.

![Login Screenshot](docs/images/login.png)
*Screenshot placeholder: Spotify login button in sidebar*

**2. Prompt Input**

Users enter a free-text description of their desired playlist.

![Input Screenshot](docs/images/input.png)
*Screenshot placeholder: Text area for playlist description*

**3. Results & Voting**

Both playlists are displayed side-by-side with links to listen on Spotify. Users vote for their preferred option.

![Results Screenshot](docs/images/results.png)
*Screenshot placeholder: Two playlist options with voting buttons*

### Technical Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Gemini JSON Parsing Failures** | Implemented retry logic (3 attempts) with exponential backoff |
| **Seed Song Hallucinations** | Validate each seed against Spotify Search API before use |
| **Spotify Rate Limits** | Batch requests where possible, implement caching |
| **Large Database Search Performance** | NumPy vectorization + `argpartition` for O(n) top-k selection |

---

## Code Overview

### Project Structure

```
Promptify/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
|
├── config/
│   ├── model_consts.py         # Feature order, playlist length, etc.
│   ├── rb_consts.py            # ReccoBeats API configuration
│   └── spotify_consts.py       # Spotify OAuth scopes
|
├── data_class/
│   └── recommendation_params.py # Pydantic models for Gemini schemas
|
├── llm/
│   └── llm_prompt_interpreter.py # Gemini API integration
|
├── pipelines/
│   ├── __init__.py             # Exports run_pipeline_v1, run_pipeline_v2
│   ├── api_pipeline.py         # Pipeline A: ReccoBeats-based
│   ├── db_pipeline.py          # Pipeline B: Local database
│   ├── search_engine.py        # Core similarity algorithms
│   └── shared.py               # Shared utilities (Gemini interpretation)
|
├── rb/
│   ├── rb_functions.py         # ReccoBeats API functions
│   └── request_sender.py       # HTTP request wrapper
|
├── songs_DB/
│   ├── preprocess.py           # Database preprocessing script
│   └── tracks_db.parquet       # Pre-processed track database
|
├── spotify/
│   ├── auth.py                 # Spotify OAuth manager
│   └── spotify_requests.py     # Spotify API wrapper classes
|
└── tests/
    ├── test_data_sync.py       # Database integrity tests
    ├── test_feature_alignment.py # Feature order consistency tests
    └── test_search_engine.py   # Search algorithm tests
```

### Key Components

**`llm/llm_prompt_interpreter.py`**

Handles communication with Google Gemini API:
- Constructs system prompts based on the target pipeline
- Enforces structured JSON output using Pydantic schemas
- Implements retry logic for failed generations

**`pipelines/search_engine.py`**

Contains the core similarity algorithms:
- `_calculate_weighted_distance()`: Vectorized weighted Euclidean distance
- `rank_reccobeats_candidates()`: Re-ranks API results (for Pipeline A)
- `search_db()`: Searches the local Parquet database (for Pipeline B)

**`data_class/recommendation_params.py`**

Defines Pydantic models for Gemini's structured output:
- `AudioFeatures`: Target values for each audio dimension
- `FeatureWeights`: Importance weights for ranking
- `LocalSearchParams`: Schema for Pipeline B (no seeds)
- `ReccoBeatsParams`: Schema for Pipeline A (includes seeds)

---

## Conclusions

<!-- CONCLUSIONS_PLACEHOLDER_START -->
*Final conclusions will be written based on experimental results.*

### Preliminary Observations

Based on initial testing:

1. **Response Time:** Pipeline B (Local) is consistently faster since it doesn't require external API calls.

2. **Seed Quality:** Pipeline A's effectiveness heavily depends on Gemini's ability to suggest valid, relevant seed songs.

3. **Diversity vs. Precision:** Pipeline A tends to produce more diverse results due to ReccoBeats' recommendation algorithm, while Pipeline B produces more precisely matched tracks.

### Limitations

- **Database Size:** The local database (~114K tracks) is smaller than Spotify's full catalog (100M+ tracks).
- **Temporal Bias:** The database reflects a snapshot in time and doesn't include new releases.
- **Popularity Data Gap:** ReccoBeats doesn't provide popularity scores, limiting that dimension for Pipeline A.

### Future Improvements

1. **Feedback Loop:** Allow users to mark individual tracks as "liked" or "disliked" to refine results.
2. **Hybrid Approach:** Combine both pipelines - use API for discovery, local DB for fine-tuning.
3. **Image Input:** Accept album art or mood board images as input using multimodal LLMs.
4. **Larger Database:** Integrate with Spotify's full catalog through their Recommendations API.

<!-- CONCLUSIONS_PLACEHOLDER_END -->

---

## Usage

1. Navigate to this URL:
    ```bash
    https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app
    ```

2. Click the **"Login with Spotify"** button in the sidebar

3. Sign in to your Spotify account and authorize the application

4. Enter a playlist description (e.g., "chill lo-fi beats for studying late at night")

5. Click **"Generate"** and wait for both playlists to be created

6. Listen to both playlists on Spotify and vote for the one that better matches your description

---

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [ReccoBeats API Documentation](https://reccobeats.com/docs/documentation/introduction)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Spotipy Library](https://spotipy.readthedocs.io/)
- [Spotify songs DB](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
