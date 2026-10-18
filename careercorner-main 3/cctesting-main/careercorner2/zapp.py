import os
from pathlib import Path
import sqlite3
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from services.authentication import init_db, login_ui, register_ui, google_login_button, get_redirect_uri, DB_PATH
from services.langfuse_helper import get_user_id
from pages.student_dashboard import render_student_dashboard
from styles import apply_custom_css
from utils.database import load_user_quiz
import traceback
import warnings
warnings.filterwarnings("ignore", message=".*Session State.*|.*widget with key.*")


st.set_page_config(
    page_title="Okay, now what",
    page_icon="✎ᝰ..",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

apply_custom_css()
load_dotenv()

if "reports" not in st.session_state:
    st.session_state.reports = {
        "degree": [],
        "career_quiz": [],
        "grades": [],
    }

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "universities_2025_1f.csv"

@st.cache_resource
def load_dges_df():
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    return pd.DataFrame()

if "universities_df" not in st.session_state:
    st.session_state["universities_df"] = load_dges_df()

if st.session_state["universities_df"].empty and not DATA_PATH.exists():
    st.error("DGES data not found")

conn = init_db()

if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "username" not in st.session_state:
    st.session_state.username = None
if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = None

query_params = st.query_params

if "code" in query_params and not st.session_state.get("logged_in", False):
    code = query_params["code"]
    if isinstance(code, list):
        code = code[0]

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = get_redirect_uri()

    try:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        token_resp = requests.post(token_url, data=token_data)
        token_json = token_resp.json()

        if "access_token" in token_json:
            access_token = token_json["access_token"]
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            userinfo_resp = requests.get(userinfo_url, headers=headers)
            user_data = userinfo_resp.json()

            email = user_data.get("email", "").strip().lower()
            username = email  # one id per student: the lowercase email, same as local login
            display_name = user_data.get("name", "Unknown User")
            
            # Save to database if new user
            from services.authentication import get_user_by_username, create_user
            from utils.db import connect
            with connect() as conn:
                existing_user = get_user_by_username(conn, email)
                if not existing_user:
                    create_user(conn, username, display_name, email, "google_oauth_placeholder")

            st.session_state.logged_in = True
            st.session_state.user = {
                "display_name": display_name,
                "email": email,
                "username": username,
            }
            st.session_state.username = username
            st.query_params.clear()
            st.success(f"✓ Logged in as {display_name}")
            st.rerun()
        else:
            error_msg = token_json.get('error_description', token_json.get('error', 'Unknown error'))
            st.error(f"Google login failed: {error_msg}")
            st.query_params.clear()
    except Exception as e:
        st.error(f"OAuth error: {str(e)}")
        st.query_params.clear()

# Track if this is first render after login
if "welcome_animated" not in st.session_state:
    st.session_state.welcome_animated = False

@st.dialog("Welcome")
def login_modal():
    _logo_l, _logo_c, _logo_r = st.columns([1, 3, 1])
    with _logo_c:
        st.image(str(BASE_DIR / "data" / "okaynowwhatlogo2.png"), width="stretch")

    st.caption("Please log in or register to continue")

    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.write("Sign in with Google:")
        google_login_button()
        st.write("Or use local login:")
        login_ui()
    with tab2:
        register_ui()

    st.markdown("---")
    if st.button("Continue as guest", key="guest_btn", width="stretch"):
        import uuid
        gid = f"guest-{uuid.uuid4().hex[:8]}"
        st.session_state.logged_in = True
        st.session_state.user_id = gid
        st.session_state.username = gid
        st.session_state.user = {"display_name": "Guest", "email": "", "username": gid, "is_guest": True}
        st.rerun()

# SHOW LOGIN MODAL FIRST - Don't render anything else until logged in
if not st.session_state.get("logged_in") or not st.session_state.user:
    login_modal()
    st.stop()

# NOW USER IS LOGGED IN - Load their data
if st.session_state.get("logged_in") and st.session_state.user:
    user_id = get_user_id()
    is_guest = st.session_state.user.get("is_guest", False)
    quiz_row = None if is_guest else load_user_quiz(user_id)
    if quiz_row:
        st.session_state.quiz_result = quiz_row

    with st.sidebar:
        BASE_DIR = Path(__file__).parent
        st.image(BASE_DIR / "data" / "okaynowwhatlogo_white.png", width='stretch')
        st.success(f"Logged in as {st.session_state.user['display_name']}")

        def logout():
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_type = None
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.welcome_animated = False  # Reset animation flag

        st.button("Logout", on_click=logout)
        st.markdown("---")

# STUDENT DASHBOARD
if st.session_state.get("logged_in") and st.session_state.user:
    st.sidebar.title("Student Menu")

    STUDENT_OPTIONS = [
        "Dashboard",
        "Career Quiz",
        "Degree Picker",
        "Grades Analysis",
        "University Finder",
        "Resources",
        "My Reports"
    ]

    redirect_target = st.session_state.get("redirect_to")
    if redirect_target and redirect_target in STUDENT_OPTIONS:
        st.session_state.student_choice = redirect_target
        del st.session_state.redirect_to
        st.rerun()

    current = st.session_state.get("student_choice", "Dashboard")
    if current not in STUDENT_OPTIONS:
        current = "Dashboard"

    choice = st.sidebar.radio(
        "Go to:",
        STUDENT_OPTIONS,
        index=STUDENT_OPTIONS.index(current),
        key="student_choice",
    )

    render_student_dashboard(choice)
