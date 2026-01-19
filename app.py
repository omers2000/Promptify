"""
Promptify - Music Recommendation Comparison App
"""

import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# --- Local Imports ---
from spotify.spotify_requests import UserRequests, SearchRequests
from config.spotify_consts import SCOPE
from pipelines import run_pipeline_v1, run_pipeline_v2
from spotify.auth import Auth

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

SHEET_ID = "1l-iMIcJhzhHIiFUqJFM6Dm1RgMYds4WEhrpl-XwZkWc"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ============================================================
# STATE MANAGEMENT
# ============================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "token_info": None,
        "user_profile": None,
        "current_prompt": "",
        "show_results": False,
        "is_generating": False,
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
# AUTHENTICATION LOGIC
# ============================================================

def get_auth_manager():
    """Creates a SpotifyOAuth manager with correct signature."""
    # 1. Fetch Secrets
    client_id = st.secrets.get("SP_CLIENT_ID") or os.getenv("SP_CLIENT_ID")
    client_secret = st.secrets.get("SP_CLIENT_SECRET") or os.getenv("SP_CLIENT_SECRET")
    redirect_uri = st.secrets.get("REDIRECT_URI") or os.getenv("REDIRECT_URI")
    
    if not redirect_uri:
        st.error("❌ Missing REDIRECT_URI in Secrets.")
        st.stop()
        
    # 2. Define Cache Path (Restored from your original code)
    # We use a fixed path because on Streamlit Cloud, files are ephemeral anyway.
    cache_path = ".spotify_cache"

    # 3. Initialize Auth (Restored signature)
    return Auth(
        client_id,
        client_secret,
        redirect_uri,
        SCOPE,
        cache_path  # <--- Added this back
    )

def handle_oauth_callback():
    """Captures the 'code' from URL immediately on app load."""
    if "code" in st.query_params:
        # Debugging: Show that we caught the code
        with st.expander("🔌 Connection Debugging", expanded=False):
            st.write("Code found in URL, attempting exchange...")
            
        auth_manager = get_auth_manager().auth_manager
        
        try:
            code = st.query_params["code"]
            token_info = auth_manager.get_access_token(code)
            
            if token_info:
                st.session_state.token_info = token_info
                # Clear URL and Rerun
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Token exchange returned None.")
                
        except Exception as e:
            st.error(f"❌ Login Error: {e}")
            # Do not clear params here so you can see the error

def get_spotify_client():
    """Returns authenticated client or None."""
    if not st.session_state.token_info:
        return None
    
    token_info = st.session_state.token_info
    auth_obj = get_auth_manager()
    auth_manager = auth_obj.auth_manager

    # Check if token is expired
    try:
        if auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            st.session_state.token_info = token_info
    except Exception as e:
        # If refresh fails, kill the session
        st.warning(f"Session expired, please log in again. ({e})")
        st.session_state.token_info = None
        return None

    spotify = auth_obj.get_client(token_info["access_token"])
    
    return {
        "spotify": spotify,
        "user_requests": UserRequests(spotify),
        "search_requests": SearchRequests(spotify)
    }

# ============================================================
# UI COMPONENTS
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.header("🔐 Spotify Auth")
        
        client_tools = get_spotify_client()
        
        if client_tools:
            # --- LOGGED IN ---
            try:
                if not st.session_state.user_profile:
                    st.session_state.user_profile = client_tools["user_requests"].get_profile()
                
                profile = st.session_state.user_profile
                st.success(f"Connected: **{profile['display_name']}**")
                
                if st.button("Disconnect"):
                    st.session_state.token_info = None
                    st.session_state.user_profile = None
                    # Clean cache file if it exists
                    if os.path.exists(".spotify_cache"):
                        os.remove(".spotify_cache")
                    st.rerun()

            except Exception:
                st.session_state.token_info = None
                st.rerun()
                
        else:
            # --- LOGGED OUT ---
            auth_manager = get_auth_manager().auth_manager
            # Get Auth URL
            auth_url = auth_manager.get_authorize_url()
            
            st.link_button("👉 Log in with Spotify", auth_url, type="primary")
            
            # Debugging info
            with st.expander("Troubleshoot"):
                st.write(f"Redirect URI: `{st.secrets.get('REDIRECT_URI')}`")
                st.write("Ensure this matches your Spotify Dashboard exactly.")

        st.divider()
        st.markdown("### How to Vote\n1. Generate Playlists\n2. Listen on Spotify\n3. Click 'Option A', 'B', or 'Tie'")

def render_input_area():
    st.header("📝 Describe Your Playlist")
    
    prompt = st.text_area(
        "Mood / Genre / Vibe:", 
        value=st.session_state.current_prompt,
        height=100
    )
    st.session_state.current_prompt = prompt
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        is_logged_in = st.session_state.token_info is not None
        if st.button("🎲 Generate", type="primary", disabled=not is_logged_in, use_container_width=True):
            if not st.session_state.current_prompt.strip():
                st.error("⚠️ Please enter a playlist description")
            else:
                run_generation_logic()

# ============================================================
# LOGIC & RESULTS
# ============================================================

def run_generation_logic():
    if st.session_state.is_generating: return
    st.session_state.is_generating = True
    
    client_tools = get_spotify_client()
    prompt = st.session_state.current_prompt
    
    st.session_state.show_results = False
    st.session_state.vote_submitted = False
    st.session_state.vote_success = False
    st.session_state.v1_results = None
    st.session_state.v2_results = None
    st.session_state.v1_error = None
    st.session_state.v2_error = None
    
    with st.spinner("Generating Option A (API)..."):
        try:
            st.session_state.v1_results = run_pipeline_v1(prompt, client_tools["search_requests"])
        except Exception as e:
            st.session_state.v1_error = str(e)

    with st.spinner("Generating Option B (DB)..."):
        try:
            st.session_state.v2_results = run_pipeline_v2(prompt)
        except Exception as e:
            st.session_state.v2_error = str(e)
            
    if st.session_state.v1_results:
        st.session_state.playlist_a_url = create_playlist_wrapper("A", st.session_state.v1_results["track_ids"], client_tools["user_requests"])
    if st.session_state.v2_results:
        st.session_state.playlist_b_url = create_playlist_wrapper("B", st.session_state.v2_results["track_ids"], client_tools["user_requests"])

    st.session_state.show_results = True
    st.session_state.is_generating = False
    st.rerun()

def get_gsheet_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            return gspread.authorize(creds)
        credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        if os.path.exists(credentials_path):
            creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
            return gspread.authorize(creds)
        return None
    except Exception: return None

def save_vote_to_sheet(vote_type):
    client = get_gsheet_client()
    if not client: return
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        v1_ids = st.session_state.v1_results["track_ids"] if st.session_state.v1_results else []
        v2_ids = st.session_state.v2_results["track_ids"] if st.session_state.v2_results else []
        row = [datetime.now().isoformat(), st.session_state.current_prompt, vote_type, len(v1_ids), len(v2_ids), ";".join(v1_ids), ";".join(v2_ids)]
        sheet.append_row(row)
        st.session_state.vote_success = True
        st.session_state.vote_submitted = True
    except Exception: st.session_state.vote_success = False

def create_playlist_wrapper(option_name, track_ids, user_requests):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        playlist_name = f"Promptify Option {option_name} - {timestamp}"
        playlist = user_requests.create_playlist(name=playlist_name, songs=track_ids)
        return playlist.get("external_urls", {}).get("spotify")
    except Exception: return None

def render_results():
    if not st.session_state.show_results: return
    st.divider()
    st.header("🎯 Results")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎵 Option A")
        if st.session_state.v1_error: st.error(st.session_state.v1_error)
        elif st.session_state.v1_results:
            if st.session_state.playlist_a_url: st.link_button("🔗 Open Playlist A", st.session_state.playlist_a_url, use_container_width=True)
            with st.expander("Show Tracks"): st.write(st.session_state.v1_results["track_ids"])
    with col2:
        st.subheader("🎵 Option B")
        if st.session_state.v2_error: st.error(st.session_state.v2_error)
        elif st.session_state.v2_results:
            if st.session_state.playlist_b_url: st.link_button("🔗 Open Playlist B", st.session_state.playlist_b_url, use_container_width=True)
            with st.expander("Show Tracks"): st.write(st.session_state.v2_results["track_ids"])
    if st.session_state.v1_results and st.session_state.v2_results: render_voting_buttons()

def render_voting_buttons():
    st.divider()
    st.header("🗳️ Cast Your Vote")
    if st.session_state.vote_submitted:
        st.success("✅ Vote Saved!") if st.session_state.vote_success else st.error("❌ Error saving vote.")
        if st.button("Start Over"):
            st.session_state.show_results = False
            st.session_state.current_prompt = ""
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        with c1: st.button("👈 Option A is Better", use_container_width=True, on_click=save_vote_to_sheet, args=("V1",))
        with c2: st.button("🤝 It's a Tie", use_container_width=True, on_click=save_vote_to_sheet, args=("tie",))
        with c3: st.button("👉 Option B is Better", use_container_width=True, on_click=save_vote_to_sheet, args=("V2",))

# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title="Promptify", page_icon="🎵", layout="wide")
    
    init_session_state()
    
    # 1. Check for Login Code Immediately
    handle_oauth_callback()
    
    st.title("🎵 Promptify")
    render_sidebar()
    render_input_area()
    render_results()

if __name__ == "__main__":
    main()