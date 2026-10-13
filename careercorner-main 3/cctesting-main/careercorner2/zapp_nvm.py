import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from services.authentication import init_db, login_ui, register_ui, google_login_button
from services.langfuse_helper import get_user_id
from pages.student_dashboard import render_student_dashboard
from pages.professional_dashboard import render_professional_dashboard
from styles import apply_custom_css
from utils.database import load_user_cv, load_user_quiz
import warnings
warnings.filterwarnings("ignore", message=".*Session State.*|.*widget with key.*")


st.set_page_config(
    page_title="Career Corner",
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

# reset function to go back to main welcome screen
def reset():
    st.session_state.user_type = None

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

print("hello world!")

query_params = st.query_params

if "code" in query_params and not st.session_state.get("logged_in", False):
    code = query_params.get("code")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Auto-detect environment (same logic)
    if os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud":
        REDIRECT_URI = os.getenv("REDIRECT_URI")
    else:
        REDIRECT_URI = "http://localhost:8501"

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

        st.session_state.logged_in = True
        st.session_state.user = {
            "display_name": user_data.get("name", "Unknown User"),
            "email": user_data.get("email", ""),
            "username": user_data.get("email", "").split("@")[0]
            if user_data.get("email")
            else None,
        }
        st.session_state.username = st.session_state.user["username"]
        st.query_params.clear()
        st.rerun()
    else:
        st.warning("Google login failed. Please try again.")

# NEW: Track if this is first render after login
if "welcome_animated" not in st.session_state:
    st.session_state.welcome_animated = False

@st.dialog("⟡ Welcome to Career Corner!")
def login_modal():
    st.caption("Please log in or register to continue")

    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.write("Sign in with Google:")
        google_login_button()
        st.write("Or use local login:")
        login_ui()
    with tab2:
        register_ui()

# SHOW LOGIN MODAL FIRST - Don't render anything else until logged in
if not st.session_state.get("logged_in") or not st.session_state.user:
    login_modal()
    st.stop()  # STOP HERE - Don't render anything below

# NOW USER IS LOGGED IN - Load their data
if st.session_state.get("logged_in") and st.session_state.user:
    user_id = get_user_id()
    stored_cv = load_user_cv(user_id)
    if stored_cv:
        if "parsed_data" in stored_cv:
            st.session_state.cv_data = stored_cv["parsed_data"]
        elif "cv_data" in stored_cv:
            st.session_state.cv_data = stored_cv["cv_data"]
        else:
            st.session_state.cv_data = stored_cv

    quiz_row = load_user_quiz(user_id)
    if quiz_row:
        st.session_state.quiz_result = quiz_row

    with st.sidebar:
        BASE_DIR = Path(__file__).parent
        st.image(BASE_DIR / "data" / "careercornermini.png", width='stretch')
        st.success(f"Logged in as {st.session_state.user['display_name']}")

        def logout():
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_type = None
            st.session_state.user = None
            st.session_state.welcome_animated = False  # Reset animation flag

        st.button("Logout", on_click=logout)
        st.markdown("---")

# ONLY SHOW WELCOME SCREEN IF NO USER TYPE SELECTED
if st.session_state.user_type is None:
    # INJECT CSS FIRST (before any content to prevent FOUC)
    animation_css = """
    <style>
    /* Prevent flash of unstyled content */
    .welcome-fade-up {
        animation: fadeUp 1s ease-out forwards;
        opacity: 0;
        transform: translateY(30px);
    }

    .typewriter-delayed {
        font-family: DMSans;
        overflow: hidden;
        border-right: .15em solid orange;
        white-space: nowrap;
        opacity: 0;
        width: 0;
        display: inline-block;
        animation: 
            fadeIn 0.1s ease-in 0.8s forwards,
            typing 2s steps(40, end) 1s forwards, 
            blink-caret .75s step-end infinite 1s;
    }

    .buttons-fade-up {
        animation: fadeUp 1s ease-out 2.5s forwards;
        opacity: 0;
        transform: translateY(30px);
    }

    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeIn {
        to { opacity: 1; }
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }

    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: orange; }
    }
    </style>
    """
    st.markdown(animation_css, unsafe_allow_html=True)

    # Mark as animated
    if not st.session_state.welcome_animated:
        st.session_state.welcome_animated = True

    # Welcome title with fade up (using HTML to avoid Streamlit's default rendering)
    st.markdown("""
    <div class="welcome-fade-up">
        <h1>Welcome to Career Corner!</h1>
    </div>
    """, unsafe_allow_html=True)

    # Typewriter with delay
    st.markdown("""
    <p class="typewriter-delayed">Hi there! Please pick the option that best describes you to begin your career counseling journey!</p>
    """, unsafe_allow_html=True)

    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # Buttons with fade up delay - wrap in div BEFORE creating buttons
    st.markdown('<div class="buttons-fade-up">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Student", width='stretch', key="btn_student", type="primary"):
            st.session_state.user_type = "student"
            st.rerun()
    with col2:
        if st.button("Professional", width='stretch', key="btn_professional", type="primary"):
            st.session_state.user_type = "professional"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# STUDENT DASHBOARD
if (
    st.session_state.get("logged_in")
    and st.session_state.user
    and st.session_state.user_type == "student"
):
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

    # FIXED: Handle redirect BEFORE creating radio button
    redirect_target = st.session_state.get("redirect_to")
    if redirect_target and redirect_target in STUDENT_OPTIONS:
        # Set the choice directly (don't create conflict)
        choice = redirect_target
        # Clear redirect flag
        st.session_state.redirect_to = None
    else:
        # Normal flow: use radio button
        current = st.session_state.get("student_choice", "Dashboard")
        if current not in STUDENT_OPTIONS:
            current = "Dashboard"

        choice = st.sidebar.radio(
            "Go to:",
            STUDENT_OPTIONS,
            index=STUDENT_OPTIONS.index(current),
            key="student_choice",
        )

    st.sidebar.button("← Back", on_click=reset)
    render_student_dashboard(choice)

# PROFESSIONAL DASHBOARD
elif st.session_state.get("logged_in") and st.session_state.user and st.session_state.user_type == "professional":
    st.sidebar.title("Professional Menu")

    PROF_OPTIONS = [
        "Dashboard",
        "CV Analysis",
        "Career Growth",
        "Interview Prep",
        "CV Builder",
        "Your Next Steps",
        "My Reports"
    ]

    # FIXED: Handle redirect BEFORE creating radio button
    redirect_target = st.session_state.get("redirect_to")
    if redirect_target and redirect_target in PROF_OPTIONS:
        choice = redirect_target
        st.session_state.redirect_to = None
    else:
        current_prof = st.session_state.get("professional_choice", "Dashboard")
        if current_prof not in PROF_OPTIONS:
            current_prof = "Dashboard"

        choice = st.sidebar.radio(
            "Go to:",
            PROF_OPTIONS,
            index=PROF_OPTIONS.index(current_prof),
            key="professional_choice",
        )

    st.sidebar.button("← Back", on_click=reset)
    render_professional_dashboard(choice)
