"""Entry requirements of each DGES program: required entrance exams, minimum grades, the weights
of the admission grade, and the last three first-phase cut-offs. No Streamlit calls.

Source: the DGES course pages (2026 applications), collected once into
data/dges_requirements_2026.csv. One row per program, keyed by course_code and institution_name.
All grades are on the 0-200 scale.
"""
import json
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dges_requirements_2026.csv"

# DGES names an exam differently from school transcripts; both map to one key.
ALIASES = {
    "mat apl ciencias soc": "matematica aplicada as ciencias sociais",
    "matematica b": "matematica",
    "fisica e quimica a": "fisica e quimica",
    "biologia e geologia": "biologia e geologia",
    "historia da cultura e das artes": "historia da cultura e das artes",
}
RULE_COUNT = {"one_of": 1, "two_of": 2, "three_of": 3}

def _plain(text):
    text = unicodedata.normalize("NFD", str(text or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"\(\s*\d+\s*\)", " ", text)       # "(635)" exam codes
    text = re.sub(r"\bexame( nacional)?\b", " ", text)
    text = re.sub(r"[^a-z ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def exam_key(name):
    key = _plain(name)
    return ALIASES.get(key, key)

def _number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value

def _code(value):
    value = str(value).strip()
    return value[:-2] if value.endswith(".0") else value

@lru_cache(maxsize=1)
def _table():
    if not DATA_PATH.exists():
        return {}
    df = pd.read_csv(DATA_PATH, dtype={"course_code": str})
    table = {}
    for row in df.to_dict("records"):
        table[(_code(row["course_code"]), _plain(row["institution_name"]))] = row
    return table

def requirements_for(course_code, institution_name):
    """The requirements of one program, or None when DGES data for it is not available."""
    row = _table().get((_code(course_code), _plain(institution_name)))
    if row is None:
        return None
    try:
        sets = json.loads(row.get("exam_sets") or "[]")
    except ValueError:
        sets = []
    return {
        "exam_rule": row.get("exam_rule") or "all",
        "exam_sets": sets,
        "min_application": _number(row.get("min_application")),
        "min_exams": _number(row.get("min_exams")),
        "w_secondary": _number(row.get("w_secondary")),
        "w_exams": _number(row.get("w_exams")),
        "last_grade_2023": _number(row.get("last_grade_2023_f1")),
        "last_grade_2024": _number(row.get("last_grade_2024_f1")),
        "candidates_2025": _number(row.get("candidates_2025")),
        "places_2025": _number(row.get("vagas_2025")),
    }

def exam_options_text(req):
    """The accepted exams in plain words, e.g. 'Matemática A + Física e Química, or ...'."""
    rule = req["exam_rule"]
    sets = req["exam_sets"]
    if rule in RULE_COUNT and sets:
        n = RULE_COUNT[rule]
        return f"{n} of: " + ", ".join(sets[0])
    return " OR ".join(" + ".join(s) for s in sets)

def _student_exams(exams):
    """{normalised exam name: grade 0-200} from the student's exam grades (zeros ignored)."""
    out = {}
    for name, grade in (exams or {}).items():
        grade = _number(grade)
        if grade and grade > 0:
            out[exam_key(name)] = max(grade, out.get(exam_key(name), 0))
    return out

def _best_exam_set(req, have):
    """(mean grade, exams used) of the best combination the student can use, or (None, [])."""
    rule, sets = req["exam_rule"], req["exam_sets"]
    best = (None, [])
    if rule in RULE_COUNT and sets:
        pool = sorted(((have[exam_key(n)], n) for n in sets[0] if exam_key(n) in have), reverse=True)
        need = RULE_COUNT[rule]
        if len(pool) >= need:
            used = pool[:need]
            best = (sum(g for g, _ in used) / need, [n for _, n in used])
        return best
    for combo in sets:
        if combo and all(exam_key(n) in have for n in combo):
            mean = sum(have[exam_key(n)] for n in combo) / len(combo)
            if best[0] is None or mean > best[0]:
                best = (mean, list(combo))
    return best

def admission_for(req, secondary_200, exams):
    """The student's admission grade for one program, using that program's own formula.

    secondary_200: school average on the 0-200 scale. exams: {name: 0-200}.
    Returns a dict with status 'ok', 'needs_exam' (no usable exam combination yet) or
    'no_requirements'.
    """
    if not req or not req.get("w_secondary") or not req.get("w_exams"):
        return {"status": "no_requirements"}
    have = _student_exams(exams)
    mean, used = _best_exam_set(req, have)
    if mean is None:
        return {"status": "needs_exam", "exams_needed": exam_options_text(req)}
    grade = (req["w_secondary"] * secondary_200 + req["w_exams"] * mean) / 100.0
    problems = []
    if req["min_exams"] and mean < req["min_exams"]:
        problems.append(f"entrance exam average {mean:.1f} is below the minimum {req['min_exams']:g}")
    if req["min_application"] and grade < req["min_application"]:
        problems.append(f"admission grade {grade:.1f} is below the minimum {req['min_application']:g}")
    return {
        "status": "ok",
        "admission_grade_200": round(grade, 1),
        "exams_used": used,
        "exam_average_200": round(mean, 1),
        "formula": f"{req['w_secondary']:g}% school average + {req['w_exams']:g}% entrance exams",
        "meets_minimums": not problems,
        "problems": problems,
    }

def competition_text(req):
    cand, places = req.get("candidates_2025"), req.get("places_2025")
    if cand and places:
        return f"{cand:g} candidates for {places:g} places in 2025 (1st phase)"
    return None
