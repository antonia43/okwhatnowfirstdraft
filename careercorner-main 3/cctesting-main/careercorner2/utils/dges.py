"""Shared DGES helpers: the programs table and text matching. No Streamlit calls.

The table (data/universities_2025_1f.csv) has one row per program with
course_code, institution_name, course_name, degree_type, placed, last_grade
(0-200 scale), region, type, lat and lon.
"""
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "universities_2025_1f.csv"


def normalize_text(text):
    """Remove accents and normalize text for matching."""
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower()


@lru_cache(maxsize=1)
def _read_csv(path):
    return pd.read_csv(path)


def load_dges_df():
    """The DGES programs table (a copy). Empty DataFrame if the CSV is missing."""
    if not DATA_PATH.exists():
        return pd.DataFrame()
    return _read_csv(str(DATA_PATH)).copy()


def find_programs(degree_name, df=None):
    """Programs whose course name contains degree_name (accent and case insensitive)."""
    if df is None:
        df = load_dges_df()
    if df is None or df.empty or not str(degree_name or "").strip():
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    wanted = normalize_text(degree_name).strip()
    names = df["course_name"].apply(normalize_text)
    return df[names.str.contains(wanted, regex=False)]
