import os
import streamlit as st
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config.spotify_consts import SCOPE
from spotify.spotify_requests import UserRequests, SearchRequests
from pipelines import run_pipeline_v1, run_pipeline_v2
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# ============================================================
# 1. ROBUST AUTH MANAGER (Cached)
# ============================================================

@st.cache_resource
def get_auth_manager():
    """
    Creates a Cached SpotifyOAuth Object.
    This persists across reruns so it doesn't 'forget' the authentication state.
    """
    # 1. Try Secrets (Cloud) -> Fallback to Env (Local)
    client_id = st.secrets.get("SP_CLIENT_ID") or os.getenv("SP_CLIENT_ID")
    client_secret = st.secrets.get("SP_CLIENT_SECRET") or os.getenv("SP_CLIENT_SECRET")
    redirect_uri = st.secrets.get("REDIRECT_URI") or os.getenv("REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        return None

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=None, # Disable file cache to rely purely on session state
        show_dialog=True
    )

# ============================================================
# 2. APP LOGIC
# ============================================================

def main():
    st.set_page_config(page_title="Promptify Debug", page_icon="🐞")
    
    # --- Session State Init ---
    if "token_info" not in st.session_state:
        st.session_state.token_info = None

    sp_oauth = get_auth_manager()

    # --- DEBUG CONSOLE (Top of App) ---
    with st.expander("🔍 Debug Console", expanded=True):
        if not sp_oauth:
            st.error("❌ Secrets Missing! Check SP_CLIENT_ID, SP_CLIENT_SECRET, REDIRECT_URI")
            st.stop()
            
        st.write(f"**Redirect URI Configured:** `{sp_oauth.redirect_uri}`")
        
        # Check URL Parameters
        query_params = st.query_params
        code = query_params.get("code")
        
        st.write(f"**URL Code Parameter:** `{str(code)[:10]}...`" if code else "❌ None")
        st.write(f"**Current Session Token:** {'✅ Valid' if st.session_state.token_info else '❌ None'}")

        # --- THE FIX: MANUAL TOKEN EXCHANGE ---
        # If we have a code but no token, try to swap it.
        if code and not st.session_state.token_info:
            try:
                st.info("🔄 Attempting to exchange code for token...")
                token_info = sp_oauth.get_access_token(code)
                st.session_state.token_info = token_info
                st.success("✅ Token acquired! Refreshing...")
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Token Exchange Failed: {e}")
                st.write("Tip: If this says 'Bad Request', your Redirect URI in Streamlit Secrets might not match Spotify Dashboard exactly.")

    # --- MAIN UI ---
    st.title("🎵 Promptify (Debug Mode)")

    if not st.session_state.token_info:
        # SHOW LOGIN BUTTON
        auth_url = sp_oauth.get_authorize_url()
        st.link_button("👉 Log in with Spotify", auth_url, type="primary")
        st.info("Click above. If it just reloads this page without logging in, check the Debug Console above.")
    else:
        # LOGGED IN SUCCESS
        st.success("You are logged in!")
        
        # Create Client
        sp = spotipy.Spotify(auth=st.session_state.token_info['access_token'])
        user = sp.current_user()
        st.write(f"Welcome, **{user['display_name']}**")
        
        if st.button("Log Out"):
            st.session_state.token_info = None
            st.rerun()

        # --- YOUR APP LOGIC GOES HERE ---
        # (I've hidden the complex logic for a moment to verify auth works first)
        render_app_features(sp)

def render_app_features(sp):
    """Rest of your app logic (Prompt input, pipelines, etc.)"""
    st.divider()
    prompt = st.text_area("Describe your playlist vibe:")
    if st.button("Generate"):
        st.write(f"Processing: {prompt}")
        # Call your pipelines here normally
        # run_pipeline_v1(...)

if __name__ == "__main__":
    main()