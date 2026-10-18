import base64
import streamlit as st
from pathlib import Path

# ---- Theme palette (dark blue + purple) ----
NAVY_DEEP = "#0A0E3D"
NAVY = "#0E1450"
NAVY_LIGHT = "#1B1F6B"
INDIGO = "#3B2BD9"
PURPLE = "#7B2FF7"
PURPLE_LIGHT = "#A855F7"
MAGENTA = "#C026D3"
LAVENDER = "#D9C7FF"
TEXT = "#FFFFFF"
TEXT_MUTED = "#C9C6F2"


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
    # main page background image (kept subtle so it sits under the dark gradient)
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
            opacity: 0.12;
            mix-blend-mode: screen;
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
            opacity: 0.06;
            mix-blend-mode: screen;
            pointer-events: none;
            z-index: 0;
        }}
        """

    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@600;700;800&display=swap');

    /* Global */
    .stApp {{
        background: linear-gradient(160deg, {NAVY_DEEP} 0%, {NAVY} 55%, #1A0F5C 100%);
        background-attachment: fixed;
        color: {TEXT};
        font-family: 'Barlow', sans-serif;
    }}

    {background_image_css}

    .main .block-container {{
        background: linear-gradient(180deg, rgba(20, 24, 100, 0.72) 0%, rgba(12, 14, 60, 0.82) 100%);
        backdrop-filter: blur(6px);
        border-radius: 22px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(123, 47, 247, 0.25);
        border: 1px solid rgba(168, 85, 247, 0.35);
        position: relative;
        z-index: 1;
        animation: fadeIn 0.5s ease-out;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(200deg, {NAVY_LIGHT} 0%, {NAVY_DEEP} 70%) !important;
        border-right: 1px solid rgba(168, 85, 247, 0.35);
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
        color: {TEXT_MUTED} !important;
        font-weight: 500;
        font-family: 'Barlow', sans-serif;
        position: relative;
        z-index: 1;
    }}

    section[data-testid="stSidebar"] .stRadio > label {{
        color: {TEXT} !important;
        font-size: 1.1rem;
        font-weight: 600;
    }}

    section[data-testid="stSidebar"] .stRadio > div {{
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 15px;
        padding: 10px;
        position: relative;
        z-index: 1;
    }}

    section[data-testid="stSidebar"] [role="radiogroup"] label {{
        color: {TEXT_MUTED} !important;
        padding: 10px 15px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }}

    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background: linear-gradient(90deg, rgba(123, 47, 247, 0.55), rgba(192, 38, 211, 0.25));
        color: {TEXT} !important;
        transform: translateX(5px);
    }}

    /* Buttons */
    .stButton > button {{
        background: rgba(255, 255, 255, 0.08) !important;
        color: {TEXT} !important;
        border: 1px solid rgba(168, 85, 247, 0.6) !important;
        border-radius: 15px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 12px rgba(123, 47, 247, 0.25) !important;
        font-family: 'Barlow', sans-serif !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.55) !important;
        background: rgba(168, 85, 247, 0.25) !important;
        border-color: {PURPLE_LIGHT} !important;
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {INDIGO} 0%, {PURPLE} 55%, {MAGENTA} 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(123, 47, 247, 0.5) !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, {PURPLE} 0%, {MAGENTA} 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(192, 38, 211, 0.6) !important;
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        background-color: rgba(255, 255, 255, 0.07) !important;
        color: {TEXT} !important;
        border: 1px solid rgba(168, 85, 247, 0.45) !important;
        position: relative;
        z-index: 1;
    }}

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    [data-testid="stChatInput"] textarea {{
        background-color: rgba(10, 14, 61, 0.85) !important;
        color: {TEXT} !important;
        border: 1px solid rgba(168, 85, 247, 0.4) !important;
        border-radius: 12px !important;
    }}

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    [data-testid="stChatInput"] textarea:focus {{
        border-color: {PURPLE_LIGHT} !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.35) !important;
    }}

    [data-testid="stChatInput"] {{
        background-color: transparent !important;
    }}

    label, .stMarkdown, .stCaption, small {{
        color: {TEXT_MUTED} !important;
    }}

    /* Chat bubbles */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 16px;
    }}

    /* Expanders, tabs, alerts */
    [data-testid="stExpander"] {{
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 14px;
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {TEXT_MUTED};
    }}

    .stTabs [aria-selected="true"] {{
        color: {TEXT} !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background: linear-gradient(90deg, {PURPLE}, {MAGENTA}) !important;
    }}

    /* Headers + text */
    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT} !important;
        font-weight: 700 !important;
        font-family: 'Barlow Condensed', sans-serif !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }}

    h1 {{
        font-size: 2.8rem !important;
        margin-bottom: 1rem !important;
        background: linear-gradient(90deg, #FFFFFF 0%, {LAVENDER} 60%, {PURPLE_LIGHT} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    p, span, div {{
        font-family: 'Barlow', sans-serif !important;
    }}

    a {{
        color: {PURPLE_LIGHT} !important;
    }}

    /* Fix Material icon text like 'keyboard_arrow_down' globally */
    span[data-testid="stIconMaterial"] {{
        font-size: 0;
    }}
    span[data-testid="stIconMaterial"]::before {{
        content: ">";
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
        background: linear-gradient(160deg, rgba(59, 43, 217, 0.45) 0%, rgba(123, 47, 247, 0.25) 100%);
        border: 1px solid rgba(168, 85, 247, 0.5);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 6px 22px rgba(123, 47, 247, 0.3);
        font-family: 'Barlow', sans-serif;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">{icon}</div>
        <div style="font-size: 0.95rem; color: {LAVENDER}; font-weight: 600; margin-bottom: 5px; letter-spacing: 0.04em; text-transform: uppercase;">{title}</div>
        <div style="font-size: 2.2rem; color: {TEXT}; font-weight: 700;">{value}</div>
    </div>
    """
    return st.markdown(card_html, unsafe_allow_html=True)


def create_progress_bar(percentage, label="Progress", color="purple"):
    colors = {
        "purple": f"linear-gradient(90deg, {INDIGO}, {PURPLE}, {MAGENTA})",
        "blue": f"linear-gradient(90deg, #2B3BE0, {INDIGO})",
        "pink": f"linear-gradient(90deg, {PURPLE}, #E879F9)",
        # old names still work so existing calls don't break
        "yellow": f"linear-gradient(90deg, {PURPLE}, {MAGENTA})",
        "green": f"linear-gradient(90deg, {INDIGO}, {PURPLE})",
        "orange": f"linear-gradient(90deg, {PURPLE}, #E879F9)",
    }
    color_code = colors.get(color, colors["purple"])

    progress_html = f"""
    <div style="margin: 20px 0; font-family: 'Barlow', sans-serif;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: 600; color: {LAVENDER};">{label}</span>
            <span style="font-weight: 700; color: {TEXT};">{percentage}%</span>
        </div>
        <div style="
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            border: 1px solid rgba(168, 85, 247, 0.4);
        ">
            <div style="
                background: {color_code};
                width: {percentage}%;
                height: 100%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """
    return st.markdown(progress_html, unsafe_allow_html=True)
