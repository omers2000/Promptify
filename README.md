# Promptify: AI-Powered Playlist Generation
**Daniel Laroz and Omer Shapira**

## Live Demo
[https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app](https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app)

---

## Introduction

### Background and Motivation

Current music streaming platforms, such as Spotify, predominantly rely on metadata-based search mechanisms. Users are typically limited to querying by specific artist names, track titles, distinct genres, or a finite set of predefined tags. Consequently, finding a suitable playlist often requires a manual, exhaustive search process: users must browse through numerous suggested playlists, filtering them one by one to find a match that aligns with their preferences. This process imposes a significant cognitive load and consumes valuable time, often resulting in a compromise where the user settles for an imperfect playlist.

Moreover, human musical desires are frequently expressed through abstract concepts involving "atmosphere," "vibes," or complex scenarios (e.g., "songs for a melancholic drive on a rainy night"). Existing keyword-based search algorithms struggle to interpret these semantic nuances, failing to map abstract descriptions to the appropriate musical content.

### Project Goals

The objective of "Promptify" is to automate the translation of abstract user intent into a concrete, curated list of tracks. The solution utilizes the advanced Natural Language Processing (NLP) capabilities of modern AI (Google Gemini) to analyze the user's free-text prompt. The system distills this text into quantifiable audio parameters and features, which serve as the foundation for the search and retrieval process.

### Research Question

**Which approach yields better playlist recommendations: an API-based method that leverages external recommendation algorithms, or a local database search using weighted similarity metrics?**

Beyond the system implementation, this project focuses on a comparative study of two algorithmic approaches to playlist generation, evaluating their effectiveness through user feedback.

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
| **Backend** | Python 3.11+ | Rich ecosystem for data science and API integration |
| **Music Data API** | ReccoBeats API | Provides recommendation endpoints with audio feature filtering |
| **Music Integration** | Spotify Web API (Spotipy) | Industry standard, rich metadata, playlist creation |
| **Local Database** | Parquet (PyArrow) | Columnar storage, fast vectorized operations with NumPy |
| **Frontend** | Streamlit | Rapid prototyping, built-in state management, easy deployment |
| **Data Collection** | Google Sheets API (gspread) | Simple vote logging, real-time collaboration |

---

## Methods & Algorithms

### The Core Challenge: Prompt Engineering

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
- **0.5** = Moderate preference
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

**Advantages:**
- Leverages ReccoBeats' recommendation algorithm
- Can discover tracks outside our local database
- Seed songs guide the recommendation toward the user's taste

**Disadvantages:**
- Dependent on external API availability
- Gemini may "hallucinate" non-existent songs
- ReccoBeats lacks popularity data, limiting that dimension

---

### Pipeline B: Local Database Search

**Description:** This pipeline performs a direct similarity search on a pre-processed local database of ~114,000 tracks using weighted Euclidean distance.

**Process:**

1. **Gemini Interpretation:** The user prompt is sent to Gemini with a simpler schema:
   - Target audio feature values
   - Feature weights
   - **No seed songs required**

2. **Database Search:** A vectorized NumPy operation calculates the weighted Euclidean distance between the target vector and all tracks in the database:

```python
# Core Algorithm: Weighted Euclidean Distance
diff = candidates_matrix - target_arr
squared_diff = diff ** 2
weighted_diff = squared_diff * weights_arr
scores = weighted_diff.sum(axis=1)  # Lower = Better match
```

3. **Result Selection:** The top 10 tracks with the lowest distance scores are selected.

**Advantages:**
- No external API dependency (offline-capable)
- Faster response times
- Full control over the ranking algorithm
- Consistent, reproducible results

**Disadvantages:**
- Limited to tracks in the local database
- No collaborative filtering or trend awareness
- Database requires periodic updates

---

### Data Preprocessing

The local database is built from a CSV dataset containing Spotify track metadata and audio features. The preprocessing pipeline (`preprocess.py`) performs:

1. **Cleaning:** Remove rows with missing values, duplicates, or invalid durations
2. **Normalization:** Scale all features to 0-1 range:
   - Tempo: divided by 250
   - Popularity: divided by 100
   - Other features: already in 0-1 range
3. **Storage:** Save as Parquet format for efficient columnar access

---

## Experimental Setup

### Methodology

We designed an A/B testing framework where users generate playlists using both pipelines simultaneously and vote for which one better matches their prompt.

**Voting Options:**
- **Option A is Better** (Pipeline A wins)
- **Option B is Better** (Pipeline B wins)
- **It's a Tie** (Both equally good)

**Important:** Users are **not told** which pipeline corresponds to which option. The assignment is randomized to prevent bias.

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
| **OAuth Token Expiration** | Auto-refresh tokens using Spotipy's built-in mechanism |
| **Large Database Search Performance** | NumPy vectorization + `argpartition` for O(n) top-k selection |

---

## Code Overview

### Project Structure

```
Promptify/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── config/
│   ├── model_consts.py         # Feature order, playlist length, etc.
│   ├── rb_consts.py            # ReccoBeats API configuration
│   └── spotify_consts.py       # Spotify OAuth scopes
├── data_class/
│   └── recommendation_params.py # Pydantic models for Gemini schemas
├── llm/
│   └── llm_prompt_interpreter.py # Gemini API integration
├── pipelines/
│   ├── __init__.py             # Exports run_pipeline_v1, run_pipeline_v2
│   ├── api_pipeline.py         # Pipeline A: ReccoBeats-based
│   ├── db_pipeline.py          # Pipeline B: Local database
│   ├── search_engine.py        # Core similarity algorithms
│   └── shared.py               # Shared utilities (Gemini interpretation)
├── rb/
│   ├── rb_functions.py         # ReccoBeats API functions
│   └── request_sender.py       # HTTP request wrapper
├── songs_DB/
│   ├── preprocess.py           # Database preprocessing script
│   └── tracks_db.parquet       # Pre-processed track database
├── spotify/
│   ├── auth.py                 # Spotify OAuth manager
│   └── spotify_requests.py     # Spotify API wrapper classes
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

### Future Work

1. **Feedback Loop:** Allow users to mark individual tracks as "liked" or "disliked" to refine results.
2. **Hybrid Approach:** Combine both pipelines - use API for discovery, local DB for fine-tuning.
3. **Image Input:** Accept album art or mood board images as input using multimodal LLMs.
4. **Larger Database:** Integrate with Spotify's full catalog through their Recommendations API.

<!-- CONCLUSIONS_PLACEHOLDER_END -->

---

## Installation & Usage

### Online (Recommended)

1. Navigate to: [https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app/](https://promptify-nlanmqgwehn5zr59dwxhlf.streamlit.app/)

2. Click the **"Login with Spotify"** button in the sidebar

3. Sign in to your Spotify account and authorize the application

4. Enter a playlist description (e.g., "chill lo-fi beats for studying late at night")

5. Click **"Generate"** and wait for both playlists to be created

6. Listen to both playlists on Spotify and vote for the one that better matches your description

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/Promptify.git
   cd Promptify
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file):
   ```env
   SP_CLIENT_ID=your_spotify_client_id
   SP_CLIENT_SECRET=your_spotify_client_secret
   REDIRECT_URI=http://localhost:8501
   GEMINI_KEY=your_google_gemini_api_key
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

---

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [ReccoBeats API Documentation](https://reccobeats.com/docs/documentation/introduction)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Spotipy Library](https://spotipy.readthedocs.io/)
