"""
Promptify - Music Recommendation Comparison App
"""
import os
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- Local Imports ---
# Ensure these match your actual folder structure
from spotify.spotify_requests import UserRequests, SearchRequests
from config.spotify_consts import SCOPE
from pipelines import run_pipeline_v1, run_pipeline_v2

# ============================================================
# 1. SETUP & AUTH MANAGER
# ============================================================

# Define Scopes explicitly here to ensure they aren't empty
# We need 'user-read-private' and 'user-read-email' to get the profile
REQUIRED_SCOPES = "user-read-private user-read-email playlist-modify-public playlist-modify-private"

@st.cache_resource
def get_auth_manager():
    """
    Creates a SpotifyOAuth manager. 
    Cached to prevent reloading secrets on every rerun.
    """
    client_id = st.secrets.get("SP_CLIENT_ID") or os.getenv("SP_CLIENT_ID")
    client_secret = st.secrets.get("SP_CLIENT_SECRET") or os.getenv("SP_CLIENT_SECRET")
    redirect_uri = st.secrets.get("REDIRECT_URI") or os.getenv("REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        st.error("❌ Secrets Missing! Check SP_CLIENT_ID, SP_CLIENT_SECRET, REDIRECT_URI")
        st.stop()

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=REQUIRED_SCOPES, # Using explicit scopes to prevent 403 errors
        cache_path=None,       # Disable file cache to force Session State usage
        show_dialog=True
    )

# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def get_valid_sp_client():
    """
    Returns an authenticated spotipy.Spotify client.
    Handles Token Refresh automatically.
    """
    if "token_info" not in st.session_state or not st.session_state.token_info:
        return None

    sp_oauth = get_auth_manager()
    token_info = st.session_state.token_info

    # check if token is expired and refresh if needed
    try:
        if sp_oauth.is_token_expired(token_info):
            # st.write("🔄 Refreshing token...") # Uncomment for debug
            token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
            st.session_state.token_info = token_info
    except Exception as e:
        st.warning(f"Session expired: {e}")
        st.session_state.token_info = None
        return None

    return spotipy.Spotify(auth=token_info["access_token"])

def sign_out():
    """Clears session and reloads."""
    st.session_state.token_info = None
    st.rerun()

# ============================================================
# 3. GOOGLE SHEETS & PIPELINES
# ============================================================

SHEET_ID = "1l-iMIcJhzhHIiFUqJFM6Dm1RgMYds4WEhrpl-XwZkWc"
GS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def save_vote_to_sheet(prompt, vote_type, v1_ids, v2_ids):
    """Saves the vote to Google Sheets."""
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=GS_SCOPES)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).sheet1
            
            row = [
                datetime.now().isoformat(),
                prompt,
                vote_type,
                len(v1_ids),
                len(v2_ids),
                ";".join(v1_ids),
                ";".join(v2_ids)
            ]
            sheet.append_row(row)
            st.toast("✅ Vote Saved!", icon="🎉")
            st.session_state.vote_submitted = True
        else:
            st.error("Missing Google Credentials in Secrets")
    except Exception as e:
        st.error(f"Save failed: {e}")

def create_playlist_link(name_suffix, track_ids, sp):
    """Creates a playlist and returns the URL."""
    try:
        user_id = sp.current_user()["id"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        name = f"Promptify {name_suffix} - {timestamp}"
        
        pl = sp.user_playlist_create(user_id, name, public=False)
        sp.playlist_add_items(pl["id"], track_ids)
        return pl["external_urls"]["spotify"]
    except Exception as e:
        st.error(f"Playlist creation failed: {e}")
        return None

# ============================================================
# 4. MAIN APP UI
# ============================================================

def main():
    st.set_page_config(page_title="Promptify", page_icon="🎵", layout="wide")

    # --- Session Init ---
    if "token_info" not in st.session_state:
        st.session_state.token_info = None
    if "vote_submitted" not in st.session_state:
        st.session_state.vote_submitted = False

    sp_oauth = get_auth_manager()

    # --- AUTH HANDLER (Runs on every load) ---
    # 1. If we have a code in URL, exchange it
    if "code" in st.query_params:
        code = st.query_params["code"]
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state.token_info = token_info
            st.query_params.clear() # Clear URL
            st.rerun()
        except Exception as e:
            st.error(f"Login Failed: {e}")
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🔐 Spotify Auth")
        sp = get_valid_sp_client()
        
        if sp:
            try:
                user = sp.current_user()
                st.success(f"Connected: **{user['display_name']}**")
                if st.button("Log Out"):
                    sign_out()
            except Exception as e:
                st.error("API Error - Try logging out")
                st.code(str(e)) # Show exact error
                if st.button("Force Log Out"):
                    sign_out()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.link_button("👉 Log in with Spotify", auth_url, type="primary")

        st.divider()
        st.markdown("### How to Vote\n1. Generate Playlists\n2. Listen on Spotify\n3. Click your preference")

    # --- MAIN CONTENT ---
    st.title("🎵 Promptify")
    
    if not sp:
        st.info("👈 Please log in via the sidebar to start generating music.")
        return

    # Input Area
    prompt = st.text_area("Mood / Genre / Vibe:", height=100)
    
    if st.button("🎲 Generate Playlists", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            st.session_state.vote_submitted = False
            st.session_state.current_prompt = prompt
            
            # --- RUN PIPELINES ---
            with st.status("Running Pipelines...", expanded=True):
                # Init Request Objects using the Valid SP client
                # Note: We pass the RAW sp client to your wrapper classes
                search_req = SearchRequests(sp) 
                
                st.write("Generating Option A (API)...")
                try:
                    res_v1 = run_pipeline_v1(prompt, search_req)
                    st.session_state.res_v1 = res_v1
                except Exception as e:
                    st.error(f"V1 Failed: {e}")
                    st.session_state.res_v1 = None
                
                st.write("Generating Option B (Database)...")
                try:
                    res_v2 = run_pipeline_v2(prompt)
                    st.session_state.res_v2 = res_v2
                except Exception as e:
                    st.error(f"V2 Failed: {e}")
                    st.session_state.res_v2 = None
                    
            st.rerun()

    # --- RESULTS DISPLAY ---
    if "res_v1" in st.session_state and st.session_state.res_v1:
        st.divider()
        col1, col2 = st.columns(2)
        
        # Helper to get IDs safely
        ids_1 = st.session_state.res_v1.get("track_ids", [])
        ids_2 = st.session_state.res_v2.get("track_ids", []) if st.session_state.res_v2 else []

        with col1:
            st.subheader("Option A")
            if ids_1:
                st.write(f"Found {len(ids_1)} tracks")
                if st.button("Create Playlist A", key="btn_a"):
                    url = create_playlist_link("Option A", ids_1, sp)
                    if url: st.link_button("Open in Spotify", url)
                with st.expander("View IDs"):
                    st.code(ids_1)

        with col2:
            st.subheader("Option B")
            if ids_2:
                st.write(f"Found {len(ids_2)} tracks")
                if st.button("Create Playlist B", key="btn_b"):
                    url = create_playlist_link("Option B", ids_2, sp)
                    if url: st.link_button("Open in Spotify", url)
                with st.expander("View IDs"):
                    st.code(ids_2)
        
        # --- VOTING ---
        st.divider()
        st.subheader("🗳️ Cast Your Vote")
        
        if st.session_state.vote_submitted:
            st.success("Thank you for voting!")
            if st.button("Start New Round"):
                for key in ['res_v1', 'res_v2', 'current_prompt']:
                    del st.session_state[key]
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.button("Option A is Better 👈", use_container_width=True, 
                         on_click=save_vote_to_sheet, args=(st.session_state.current_prompt, "V1", ids_1, ids_2))
            with c2:
                st.button("It's a Tie 🤝", use_container_width=True, 
                         on_click=save_vote_to_sheet, args=(st.session_state.current_prompt, "Tie", ids_1, ids_2))
            with c3:
                st.button("Option B is Better 👉", use_container_width=True, 
                         on_click=save_vote_to_sheet, args=(st.session_state.current_prompt, "V2", ids_1, ids_2))

if __name__ == "__main__":
    main()