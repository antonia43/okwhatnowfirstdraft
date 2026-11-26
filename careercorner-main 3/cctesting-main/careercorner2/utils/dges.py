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


DATA_PATH_2026 = DATA_PATH.parent / "universities_2026_1f.csv"
DGES_2026_URL = "https://dges.gov.pt/coloc/2026/cna26_1f_resultados.xls"
REGION_WORDS = [(("lisboa", "lisbon"), "Lisbon"), (("porto",), "Porto"), (("coimbra",), "Coimbra"),
                (("braga", "minho"), "Braga"), (("faro", "algarve"), "Faro"), (("evora",), "Évora"),
                (("aveiro",), "Aveiro"), (("beira",), "Covilhã"), (("setubal",), "Setúbal"), (("leiria",), "Leiria")]
PRIVATE_WORDS = ("privad", "catolica", "lusiada", "lusofona")


def _region_of(name):
    n = normalize_text(name)
    for words, region in REGION_WORDS:
        if any(w in n for w in words):
            return region
    return "Other"


def _type_of(name):
    n = normalize_text(name)
    if "politecnico" in n:
        return "Polytechnic"
    return "Private" if any(w in n for w in PRIVATE_WORDS) else "Public"


def _build_2026(old):
    """The 2026 1st-phase results from DGES. Adds last year's grade and map positions from the 2025 table."""
    import requests
    from io import BytesIO

    resp = requests.get(DGES_2026_URL, timeout=30)
    resp.raise_for_status()
    raw = None
    for skip in range(6):
        try:
            cand = pd.read_excel(BytesIO(resp.content), engine="xlrd", skiprows=skip)
        except Exception:
            continue
        cols = [str(c).lower() for c in cand.columns]
        if any("institu" in c for c in cols) and any("curso" in c for c in cols):
            raw = cand
            break
    if raw is None:
        return None
    names = {}
    for col in raw.columns:
        low = str(col).lower()
        if "institui" in low and "nome" in low:
            names[col] = "institution_name"
        elif "curso" in low and "nome" in low:
            names[col] = "course_name"
        elif "curso" in low and "cód" in low:
            names[col] = "course_code"
        elif "grau" in low:
            names[col] = "degree_type"
        elif low.strip() == "colocados":
            names[col] = "placed"
        elif "nota" in low and "últ" in low and "geral" in low:
            names[col] = "last_grade"
    df = raw.rename(columns=names)
    df["institution_name"] = df["institution_name"].astype(str).str.strip()
    df["course_name"] = df["course_name"].astype(str).str.strip()
    df = df[(df["institution_name"].str.len() > 3) & (df["course_name"] != "nan")].copy()
    df["course_code"] = df["course_code"].astype(str).str.strip()
    for col in ("last_grade", "placed"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["region"] = df["institution_name"].apply(_region_of)
    df["type"] = df["institution_name"].apply(_type_of)

    old = old.assign(course_code=old["course_code"].astype(str).str.strip())
    located = old.dropna(subset=["lat", "lon"])
    by_program, by_institution = {}, {}
    for r in located.itertuples():
        by_program[(r.course_code, r.institution_name)] = (r.lat, r.lon)
        by_institution.setdefault(r.institution_name, (r.lat, r.lon))
    previous = {(r.course_code, r.institution_name): r.last_grade for r in old.itertuples()}
    lats, lons, before = [], [], []
    for r in df.itertuples():
        key = (r.course_code, r.institution_name)
        spot = by_program.get(key) or by_institution.get(r.institution_name) or (None, None)
        lats.append(spot[0])
        lons.append(spot[1])
        before.append(previous.get(key))
    df["lat"], df["lon"], df["last_grade_2025"] = lats, lons, before
    keep = ["course_code", "institution_name", "course_name", "degree_type", "placed", "last_grade",
            "last_grade_2025", "region", "type", "lat", "lon"]
    return df[keep]


@lru_cache(maxsize=1)
def _current_table():
    """The 2026 table (cut-offs plus the 2025 value and map positions). Built from DGES once, then
    saved next to the 2025 file. If 2026 is not available the 2025 table is used."""
    old = _read_csv(str(DATA_PATH)).copy()
    if DATA_PATH_2026.exists():
        df = pd.read_csv(DATA_PATH_2026)
        df["year"] = 2026
        return df
    try:
        new = _build_2026(old)
    except Exception:
        new = None
    if new is not None and len(new) > 500:
        try:
            new.to_csv(DATA_PATH_2026, index=False)
        except Exception:
            pass
        new["year"] = 2026
        return new
    old["last_grade_2025"] = float("nan")
    old["year"] = 2025
    return old


def load_dges_df():
    """The DGES programs table (a copy). Empty DataFrame if the CSV is missing."""
    if not DATA_PATH.exists():
        return pd.DataFrame()
    return _current_table().copy()


def find_programs(degree_name, df=None):
    """Programs whose course name contains degree_name (accent and case insensitive)."""
    if df is None:
        df = load_dges_df()
    if df is None or df.empty or not str(degree_name or "").strip():
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    wanted = normalize_text(degree_name).strip()
    names = df["course_name"].apply(normalize_text)
    return df[names.str.contains(wanted, regex=False)]
