"""
Promptify - Music Recommendation Comparison App
Compares two recommendation pipelines: API-based (V1) vs Database-based (V2)
"""

import os
import json
from datetime import datetime
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# --- Local Imports ---
# Ensure these files exist in your project structure
from spotify.spotify_requests import UserRequests, SearchRequests
from config.spotify_consts import REDIRECT_URI, SCOPE
from pipelines import run_pipeline_v1, run_pipeline_v2

load_dotenv()

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

SHEET_ID = "1l-iMIcJhzhHIiFUqJFM6Dm1RgMYds4WEhrpl-XwZkWc"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")


# ============================================================
# STATE MANAGEMENT
# ============================================================

def init_session_state():
    """Initialize all session state variables to prevent KeyErrors."""
    defaults = {
        "spotify_auth": None,
        "current_prompt": "",
        "show_results": False,
        "v1_results": None,
        "v2_results": None,
        "v1_error": None,
        "v2_error": None,
        "playlist_a_url": None,
        "playlist_b_url": None,
        "vote_submitted": False,
        "vote_success": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================
# BACKEND SERVICES (Google Sheets & Spotify)
# ============================================================

def get_gsheet_client():
    """Get authenticated Google Sheets client."""
    try:
        # 1. Production: Check Streamlit Cloud Secrets first
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        # 2. Development: Fallback to local file (for when you run on laptop)
        elif os.path.exists(CREDENTIALS_PATH):
            creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        
        else:
            st.error("❌ Google Sheets credentials not found in Secrets or local file.")
            return None
        
        return gspread.authorize(creds)

    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
        return None

def save_vote_to_sheet(vote_type):
    """Callback: Saves vote to Google Sheets."""
    client = get_gsheet_client()
    if not client:
        return
    
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Safe retrieval of list lengths
        v1_len = len(st.session_state.v1_results["track_ids"]) if st.session_state.v1_results else 0
        v2_len = len(st.session_state.v2_results["track_ids"]) if st.session_state.v2_results else 0
        v1_str = ";".join(st.session_state.v1_results["track_ids"]) if st.session_state.v1_results else ""
        v2_str = ";".join(st.session_state.v2_results["track_ids"]) if st.session_state.v2_results else ""

        row = [
            datetime.now().isoformat(),
            st.session_state.current_prompt,
            vote_type,
            v1_len,
            v2_len,
            v1_str,
            v2_str
        ]
        sheet.append_row(row)
        
        # Update State
        st.session_state.vote_success = True
        st.session_state.vote_submitted = True
        
    except Exception as e:
        st.error(f"❌ Failed to save vote: {str(e)}")
        st.session_state.vote_success = False

def create_playlist_wrapper(option_name, track_ids, user_requests):
    """Wrapper to safely create a playlist and return URL."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        playlist_name = f"Promptify Option {option_name} - {timestamp}"
        playlist = user_requests.create_playlist(name=playlist_name, songs=track_ids)
        return playlist.get("external_urls", {}).get("spotify")
    except Exception as e:
        st.warning(f"Could not create playlist for Option {option_name}: {e}")
        return None

def get_spotify_client(username):
    """Authenticates with Spotify."""
    if st.session_state.spotify_auth and st.session_state.spotify_auth.get("username") == username:
        return st.session_state.spotify_auth

    client_id = os.getenv("SP_CLIENT_ID")
    client_secret = os.getenv("SP_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        st.error("Missing Spotify credentials in .env")
        return None
    
    cache_path = f".spotify_cache_{username}"
    
    try:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,
            cache_path=cache_path
        )
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        user_requests = UserRequests(spotify)
        search_requests = SearchRequests(spotify)
        profile = user_requests.get_profile()
        
        auth_data = {
            "username": username,
            "spotify": spotify,
            "user_requests": user_requests,
            "search_requests": search_requests,
            "profile": profile
        }
        st.session_state.spotify_auth = auth_data
        return auth_data
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        if os.path.exists(cache_path):
            os.remove(cache_path)
            st.warning("Cache cleared. Please try again.")
        return None

# ============================================================
# UI COMPONENTS
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.header("🔐 Spotify Auth")
        username = st.text_input("Username", placeholder="Enter Spotify username")
        
        if username:
            auth_data = get_spotify_client(username)
            if auth_data:
                st.success(f"Connected: **{auth_data['profile']['display_name']}**")
        
        st.divider()
        st.markdown("### How to Vote\n1. Generate Playlists\n2. Listen on Spotify\n3. Click 'Option A', 'B', or 'Tie'")

def render_input_area():
    st.header("📝 Describe Your Playlist")
    
    # Text input bound to session state
    prompt = st.text_area(
        "Mood / Genre / Vibe:", 
        value=st.session_state.current_prompt,
        height=100
    )
    # Update state immediately when user types
    st.session_state.current_prompt = prompt

    is_authed = st.session_state.spotify_auth is not None
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🎲 Generate", type="primary", use_container_width=True, disabled=not (is_authed and prompt)):
            run_generation_logic()

def run_generation_logic():
    """Runs the pipelines and updates state."""
    auth = st.session_state.spotify_auth
    prompt = st.session_state.current_prompt
    
    # Reset results state
    st.session_state.show_results = False
    st.session_state.vote_submitted = False
    st.session_state.vote_success = False
    st.session_state.v1_results = None
    st.session_state.v2_results = None
    st.session_state.v1_error = None
    st.session_state.v2_error = None
    
    # 1. Run Pipeline V1
    with st.spinner("Generating Option A (API)..."):
        try:
            st.session_state.v1_results = run_pipeline_v1(prompt, auth["search_requests"])
        except Exception as e:
            st.session_state.v1_error = str(e)

    # 2. Run Pipeline V2
    with st.spinner("Generating Option B (DB)..."):
        try:
            st.session_state.v2_results = run_pipeline_v2(prompt)
        except Exception as e:
            st.session_state.v2_error = str(e)
            
    # 3. Create Playlists
    if st.session_state.v1_results:
        st.session_state.playlist_a_url = create_playlist_wrapper("A", st.session_state.v1_results["track_ids"], auth["user_requests"])
        
    if st.session_state.v2_results:
        st.session_state.playlist_b_url = create_playlist_wrapper("B", st.session_state.v2_results["track_ids"], auth["user_requests"])

    # 4. Show results
    st.session_state.show_results = True
    st.rerun()

def render_results():
    if not st.session_state.show_results:
        return

    st.divider()
    st.header("🎯 Results")
    
    col1, col2 = st.columns(2)
    
    # Option A
    with col1:
        st.subheader("🎵 Option A")
        if st.session_state.v1_error:
            st.error(st.session_state.v1_error)
        elif st.session_state.v1_results:
            if st.session_state.playlist_a_url:
                st.link_button("🔗 Open Playlist A", st.session_state.playlist_a_url, use_container_width=True)
            with st.expander("Show Tracks"):
                st.write(st.session_state.v1_results["track_ids"])

    # Option B
    with col2:
        st.subheader("🎵 Option B")
        if st.session_state.v2_error:
            st.error(st.session_state.v2_error)
        elif st.session_state.v2_results:
            if st.session_state.playlist_b_url:
                st.link_button("🔗 Open Playlist B", st.session_state.playlist_b_url, use_container_width=True)
            with st.expander("Show Tracks"):
                st.write(st.session_state.v2_results["track_ids"])

    # Voting Section
    if st.session_state.v1_results and st.session_state.v2_results:
        render_voting_buttons()

def render_voting_buttons():
    st.divider()
    st.header("🗳️ Cast Your Vote")
    
    if st.session_state.vote_submitted:
        if st.session_state.vote_success:
            st.success("✅ Vote Saved! Thank you.")
        else:
            st.error("❌ Error saving vote.")
        
        if st.button("Start Over"):
            st.session_state.show_results = False
            st.session_state.current_prompt = ""
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("👈 Option A is Better", use_container_width=True, on_click=save_vote_to_sheet, args=("V1",))
        with c2:
            st.button("🤝 It's a Tie", use_container_width=True, on_click=save_vote_to_sheet, args=("tie",))
        with c3:
            st.button("👉 Option B is Better", use_container_width=True, on_click=save_vote_to_sheet, args=("V2",))

# ============================================================
# MAIN APP
# ============================================================

def main():
    st.set_page_config(page_title="Promptify", page_icon="🎵", layout="wide")
    init_session_state()
    
    st.title("🎵 Promptify")
    render_sidebar()
    render_input_area()
    render_results()

if __name__ == "__main__":
    main()