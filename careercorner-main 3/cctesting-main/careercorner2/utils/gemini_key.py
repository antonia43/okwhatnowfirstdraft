"""One place that finds the Gemini API key, whatever the secret was named."""
import os

KEY_NAMES = ("GOOGLE_API_KEY", "GEMINI_API_KEY")


def get_gemini_api_key():
    """The key from the environment or Streamlit secrets (GOOGLE_API_KEY or GEMINI_API_KEY), else None."""
    for name in KEY_NAMES:
        value = os.getenv(name)
        if value:
            return value
    try:
        import streamlit as st

        for name in KEY_NAMES:
            value = st.secrets.get(name)
            if value:
                return str(value)
    except Exception:
        pass
    return None
