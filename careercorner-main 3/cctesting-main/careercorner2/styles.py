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
    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stLinkButton"] a,
    .stLinkButton a,
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #8B5CF6 0%, {PURPLE_LIGHT} 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(233, 213, 255, 0.7) !important;
        border-radius: 15px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 14px rgba(168, 85, 247, 0.65), 0 0 32px rgba(168, 85, 247, 0.35) !important;
        font-family: 'Barlow', sans-serif !important;
        text-decoration: none !important;
    }}

    .stButton > button p,
    [data-testid="stFormSubmitButton"] > button p,
    [data-testid="stLinkButton"] a p,
    .stLinkButton a p,
    .stDownloadButton > button p {{
        color: #FFFFFF !important;
    }}

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover,
    [data-testid="stLinkButton"] a:hover,
    .stLinkButton a:hover,
    .stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px rgba(192, 132, 252, 0.95), 0 0 46px rgba(168, 85, 247, 0.6) !important;
        background: linear-gradient(135deg, #A78BFA 0%, #C084FC 100%) !important;
        border-color: #FFFFFF !important;
        color: #FFFFFF !important;
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
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="textarea"],
    [data-testid="stChatInput"] textarea {{
        background-color: #FFFFFF !important;
        color: #1A1A40 !important;
        -webkit-text-fill-color: #1A1A40 !important;
        border: 1px solid rgba(168, 85, 247, 0.5) !important;
        border-radius: 12px !important;
    }}

    /* password eye toggle and icons inside white inputs */
    div[data-baseweb="input"] button,
    div[data-baseweb="input"] svg {{
        background-color: transparent !important;
        color: #5B21B6 !important;
        fill: #5B21B6 !important;
    }}
    div[data-baseweb="input"] span[data-testid="stIconMaterial"]::before {{
        color: #5B21B6;
    }}

    ::placeholder {{
        color: #8A87B8 !important;
        -webkit-text-fill-color: #8A87B8 !important;
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

    /* Dialogs / modals and sidebar inner panel: dark blue, never white */
    div[data-testid="stDialog"] div[role="dialog"],
    div[data-testid="stModal"] div[role="dialog"],
    div[role="dialog"] {{
        background: linear-gradient(170deg, {NAVY_LIGHT} 0%, {NAVY_DEEP} 100%) !important;
        border: 1px solid rgba(168, 85, 247, 0.45) !important;
        box-shadow: 0 0 40px rgba(123, 47, 247, 0.4) !important;
        color: {TEXT} !important;
    }}

    [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] > div {{
        background: transparent !important;
    }}

    div[role="dialog"] hr,
    section[data-testid="stSidebar"] hr,
    hr {{
        border-color: rgba(168, 85, 247, 0.35) !important;
        background-color: rgba(168, 85, 247, 0.35) !important;
    }}

    /* Tabs */
    [data-baseweb="tab-list"] [data-baseweb="tab"] {{
        color: {TEXT_MUTED} !important;
    }}
    [data-baseweb="tab-list"] [aria-selected="true"],
    [data-baseweb="tab-list"] [aria-selected="true"] p {{
        color: #FFFFFF !important;
    }}
    [data-baseweb="tab-highlight"] {{
        background: linear-gradient(90deg, {PURPLE_LIGHT}, {MAGENTA}) !important;
        background-color: {PURPLE_LIGHT} !important;
    }}
    [data-baseweb="tab-border"] {{
        background-color: rgba(168, 85, 247, 0.3) !important;
    }}

    /* White bars: top header and bottom chat strip */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main {{
        background: transparent !important;
    }}

    header[data-testid="stHeader"],
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    [data-testid="stToolbar"] *,
    [data-testid="stHeader"] button,
    [data-testid="stHeader"] a {{
        color: {TEXT_MUTED} !important;
    }}
    [data-testid="stToolbar"] svg,
    [data-testid="stHeader"] svg {{
        fill: {TEXT_MUTED} !important;
    }}

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {{
        background: transparent !important;
    }}

    /* Chat input: dark outer shell, white text field, purple send button */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {{
        background: rgba(14, 20, 80, 0.85) !important;
        border: 1px solid rgba(168, 85, 247, 0.5) !important;
        border-radius: 18px !important;
        box-shadow: 0 0 18px rgba(123, 47, 247, 0.3) !important;
    }}
    [data-testid="stChatInput"] button,
    [data-testid="stChatInputSubmitButton"] {{
        background: linear-gradient(135deg, #8B5CF6, {PURPLE_LIGHT}) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.6) !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
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
