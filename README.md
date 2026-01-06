# Promptify

**Goal**: create spotify playlist based on user prompt.
**Outline**:
- Request user's Spotify authentication
- Getting a prompt from user
- NLP process using embedding and keyword extraction
- extract Spotify flags (from Spotify API)
- match prompt embedding to songs from Spotify (API)
- rank top matches and generate playlist
- display the playlist in the user's Spotify account.

**Technologies**:
- Spotify API

**Conventions:**
- Two Data classes, each for every version
- Same feature for both versions, later we will se if we want to add more

**TODO:**
- [ ] change the number of songs in the playlist: we ask RB to give us 40 songs, we need to put in the playlist only X songs, we need to filter the best matches from those recommendations (using rank_external_candidates in logic/search_engine.py Daniel wrote) - *Omer*
- [ ] try to find out which feature weight is better - *Both*
- [ ] implement v2.py - *Omer* (Prompt from user - Gemini - get songs from DB - cosine - create playlist)
- [ ] integrate config/model_consts.py: DEFAULT_PLAYLIST_LENGTH = 20 to your parts of the code - *Omer*
- [ ] merge feature/search-logic when you aprove - *Omer*
