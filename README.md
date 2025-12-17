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
- 

**TODO:**
- change the data class SeedInfo to list form (so we can add up to 5 seed songs) - *Daniel*
- Handle cases where the llm makes a mistake - *Daniel*
- change the seed song to id method so it will work on a list of seeds - *Omer*
- change the number of songs in the playlist: we ask RB to give us 40 songs, we need to put in the playlist only 20 songs, we need to filter the best matches from those recommendations - *Both*
- try to find out which feature weight is better - *Both*
- hide the user client and secter - *Omer*
- try to find a better way to authenticate to Spotify - *Omer*
- add the seed songs to the playlist - *Omer*
