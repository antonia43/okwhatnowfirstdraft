import base64
import streamlit as st
from pathlib import Path

def get_base64_image(image_path: str) -> str | None:
    """Converting images to base64 for CSS background."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None


BASE_DIR = Path(__file__).parent

def apply_custom_css(
    logo_path: str = "data/careercornerlogo2.png",
    bg_image_path: str = "data/bg2.png",
):
    # main page background
    bg_image_base64 = get_base64_image(BASE_DIR / bg_image_path)
    background_image_css = ""
    if bg_image_base64:
        background_image_css = f"""
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/png;base64,{bg_image_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            background-attachment: fixed;
            opacity: 0.55;
            z-index: 0;
            pointer-events: none;
        }}
        """

    sidebar_bg_base64 = get_base64_image(BASE_DIR / "data" / "crumpledpaper3.avif")
    sidebar_image_css = ""
    if sidebar_bg_base64:
        sidebar_image_css = f"""
        section[data-testid="stSidebar"]::before {{
            content: "";
            position: absolute;
            inset: 0;
            background-image: url("data:image/avif;base64,{sidebar_bg_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.15;
            pointer-events: none;
            z-index: 0;
        }}
        """


    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {{
        background-color: #FFF9C4;
        font-family: 'DM Sans', sans-serif;
    }}

    {background_image_css}

    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(130, 119, 23, 0.1);
        border: 2px solid #F0F4C3;
        position: relative;
        z-index: 1;
        animation: fadeIn 0.5s ease-out;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: #C5E1A5 !important;
        position: relative;
        overflow: hidden;
    }}

    {sidebar_image_css}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        font-size: 1.4rem !important;
    }}

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {{
        color: #33691E !important;
        font-weight: 500;
        font-family: 'DM Sans', sans-serif;
        position: relative;
        z-index: 1;
    }}

    section[data-testid="stSidebar"] .stRadio > label {{
        color: #33691E !important;
        font-size: 1.1rem;
        font-weight: 600;
    }}

    section[data-testid="stSidebar"] .stRadio > div {{
        background-color: rgba(255, 255, 255, 0.4);
        border-radius: 15px;
        padding: 10px;
        position: relative;
        z-index: 1;
    }}

    section[data-testid="stSidebar"] [role="radiogroup"] label {{
        color: #33691E !important;
        padding: 10px 15px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }}

    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background-color: rgba(255, 255, 255, 0.7);
        transform: translateX(5px);
    }}

    /* Buttons */
    .stButton > button {{
        background-color: #ffe173 !important;
        color: #33691E !important;
        border: 2px solid #FFF176 !important;
        border-radius: 15px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 10px rgba(253, 216, 53, 0.3) !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(253, 216, 53, 0.5) !important;
        background-color: #FFF176 !important;
        border-color: #FFEB3B !important;
    }}

    .stButton > button[kind="primary"] {{
        background-color: #AED581 !important;
        color: white !important;
        border: 2px solid #9CCC65 !important;
        box-shadow: 0 3px 10px rgba(156, 204, 101, 0.3) !important;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background-color: #6a9742 !important;
        border-color: #AED581 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(197, 225, 165, 0.6) !important;
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        background-color: rgba(255, 255, 255, 0.6) !important;
        color: #33691E !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important;
        position: relative;
        z-index: 1;
    }}

    /* Headers + text */
    h1, h2, h3, h4, h5, h6 {{
        color: #689F38 !important;
        font-weight: 700 !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    h1 {{
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
        color: #558B2F !important;
    }}

    p, span, div {{
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* Fix Material icon text like 'keyboard_arrow_down' globally */
    span[data-testid="stIconMaterial"] {{
        font-size: 0;
    }}
    span[data-testid="stIconMaterial"]::before {{
        content: ">";          /* change to another arrow if you like */
        font-size: 1rem;
    }}



    /* Hide only menu + footer, not header (keep sidebar toggle) */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    </style>
    """,
        unsafe_allow_html=True,
    )

def create_stat_card(title, value, icon="📊"):
    card_html = f"""
    <div style="
        background-color: white;
        border: 2px solid #C5E1A5;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(130, 119, 23, 0.1);
        font-family: 'DM Sans', sans-serif;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">{icon}</div>
        <div style="font-size: 0.9rem; color: #689F38; font-weight: 600; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 2rem; color: #558B2F; font-weight: 700;">{value}</div>
    </div>
    """
    return st.markdown(card_html, unsafe_allow_html=True)

def create_progress_bar(percentage, label="Progress", color="yellow"):
    colors = {
        "yellow": "#FFEB3B",
        "green": "#AED581",
        "orange": "#FFB74D",
    }
    color_code = colors.get(color, colors["yellow"])

    progress_html = f"""
    <div style="margin: 20px 0; font-family: 'DM Sans', sans-serif;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: 600; color: #689F38;">{label}</span>
            <span style="font-weight: 700; color: #558B2F;">{percentage}%</span>
        </div>
        <div style="
            background-color: #F0F4C3;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            border: 2px solid #E0E0E0;
        ">
            <div style="
                background-color: {color_code};
                width: {percentage}%;
                height: 100%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """
    return st.markdown(progress_html, unsafe_allow_html=True)
