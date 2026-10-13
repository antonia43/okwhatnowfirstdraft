"""University abilities for the chat: search DGES programs, save, list, remove.

Programs come from the DGES table (data/universities_2025_1f.csv). Grades are on
the 0-200 scale. When the student's grade is known each program gets a colour
for the map: green (safe), yellow (target), red (reach), grey (no cut-off known).
Searching needs no grade and no login; saving needs a login.
"""
import math

from services.chat_functions import chat_function
from services.grade_functions import _grade_to_use
from utils.dges import find_programs, load_dges_df, normalize_text
from utils.grades import compare_with_cutoff

DEGREE_LEVELS = {
    "L1": "Licenciatura (1st cycle)",
    "MI": "Integrated Master's",
    "PL": "Post-work Licenciatura",
    "PM": "Master's preparatory",
}
COLORS = {"safe": "green", "target": "yellow", "reach": "red", "unknown": "grey"}
DEFAULT_LIMIT = 30
MAX_LIMIT = 60


def _number(value):
    """A float, or None for missing / NaN values."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _text(value):
    return "" if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)


def program_from_row(row, grade_200=None):
    """One DGES row as a program the chat and the map can show."""
    last = _number(row.get("last_grade"))
    last = last if last and last > 0 else None
    lat, lon = _number(row.get("lat")), _number(row.get("lon"))
    program = {
        "course_code": _text(row.get("course_code")),
        "institution_name": _text(row.get("institution_name")),
        "program_name": _text(row.get("course_name")),
        "degree_level": DEGREE_LEVELS.get(_text(row.get("degree_type")), _text(row.get("degree_type"))),
        "region": _text(row.get("region")),
        "type": _text(row.get("type")),
        "last_grade_200": last,
        "last_grade_20": round(last / 10, 2) if last else None,
        "coordinates": {"lat": lat, "lon": lon} if lat is not None and lon is not None else None,
    }
    if grade_200 is not None:
        comparison = compare_with_cutoff(grade_200, last)
        program["chance"] = comparison["status"]
        program["margin_200"] = comparison["margin_200"]
    else:
        program["chance"] = "unknown"
        program["margin_200"] = None
    program["map_color"] = COLORS[program["chance"]]
    return program


def search_programs(degree_name, grade_200=None, region=None, limit=DEFAULT_LIMIT, df=None):
    """Programs for a degree name, highest last-placed grade first."""
    df = load_dges_df() if df is None else df
    matches = find_programs(degree_name, df)
    if region and not matches.empty:
        wanted = normalize_text(region).strip()
        matches = matches[matches["region"].apply(normalize_text).str.contains(wanted, regex=False)]
    total = len(matches)
    if total:
        matches = matches.assign(_g=matches["last_grade"].apply(lambda v: _number(v) or -1))
        matches = matches.sort_values("_g", ascending=False)
    limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    programs = [program_from_row(row, grade_200) for _, row in matches.head(limit).iterrows()]
    return {
        "degree_name": degree_name,
        "grade_used_200": grade_200,
        "total_found": total,
        "shown": len(programs),
        "without_map_pin": sum(1 for p in programs if p["coordinates"] is None),
        "universities": programs,
        "display": "map",  # the chat shows these as pins on a map of Portugal
    }


def find_program(course_code, institution_name, df=None):
    """The one DGES row for this course code at this institution, or None."""
    df = load_dges_df() if df is None else df
    if df is None or df.empty:
        return None
    same_code = df["course_code"].astype(str).str.strip() == str(course_code).strip()
    same_inst = df["institution_name"].apply(normalize_text) == normalize_text(institution_name)
    rows = df[same_code & same_inst]
    return None if rows.empty else rows.iloc[0]


def saved_record(program):
    """The dict stored in saved_universities (keeps the old keys the other code reads)."""
    last = program["last_grade_200"]
    return {
        "name": program["institution_name"],
        "program_name": program["program_name"],
        "location": program["region"],
        "type": program["type"],
        "degree_level": program["degree_level"],
        "course_code": program["course_code"],
        "last_grade_200": last,
        "average_grade_required": f"{last / 10:.2f}/20" if last else "N/A",
        "coordinates": program["coordinates"],
    }


@chat_function(
    "search_universities",
    "Find Portuguese university programs for a degree, shown as pins on a map with the last-placed grade. "
    "Works without a grade (no colours) and without a login. With a grade each pin is green (high chance), "
    "yellow (possible) or red (low chance). Uses the saved admission average unless a grade is given.",
    {"properties": {
        "degree_name": {"type": "string", "description": "Degree name, e.g. 'Engenharia Informática'"},
        "grade_200": {"type": "number", "description": "Student's grade on the 0-200 scale, if known"},
        "region": {"type": "string", "description": "Only programs in this region or city, if the student has a preference"},
        "limit": {"type": "integer", "description": f"How many programs to return (default {DEFAULT_LIMIT}, max {MAX_LIMIT})"}},
     "required": ["degree_name"]},
)
def search_universities(user_id, degree_name, grade_200=None, region=None, limit=DEFAULT_LIMIT):
    result = search_programs(degree_name, _grade_to_use(user_id, grade_200), region, limit)
    if not result["total_found"]:
        result["message"] = f"No programs found for '{degree_name}'. Try a different name."
    return result


@chat_function(
    "save_university",
    "Save a university program to the student's list. Use the course_code and institution_name exactly as "
    "returned by search_universities.",
    {"properties": {
        "course_code": {"type": "string", "description": "DGES course code from search_universities"},
        "institution_name": {"type": "string", "description": "Institution name from search_universities"}},
     "required": ["course_code", "institution_name"]},
    saves=True,
)
def save_university(user_id, course_code, institution_name):
    from utils import database

    row = find_program(course_code, institution_name)
    if row is None:
        return {"saved": False, "error": "That program was not found. Search again and use the exact course_code and institution_name."}
    program = program_from_row(row)
    if database.save_university(user_id, saved_record(program)):
        return {"saved": True, "program_name": program["program_name"], "institution_name": program["institution_name"]}
    return {"saved": False, "already_saved": True, "program_name": program["program_name"],
            "institution_name": program["institution_name"]}


@chat_function(
    "get_saved_universities",
    "List the universities the student saved, with a chance colour when their grade is known.",
)
def get_saved_universities(user_id):
    from utils import database

    grade = _grade_to_use(user_id, None)
    out = []
    for uni in database.get_saved_universities(user_id):
        last = uni.get("last_grade_200")
        item = {
            "course_code": uni.get("course_code", ""),
            "institution_name": uni.get("name", ""),
            "program_name": uni.get("program_name", ""),
            "region": uni.get("location", ""),
            "last_grade_200": last,
            "saved_at": uni.get("saved_at"),
        }
        if grade is not None:
            item["chance"] = compare_with_cutoff(grade, last)["status"]
        out.append(item)
    return {"count": len(out), "grade_used_200": grade, "universities": out}


@chat_function(
    "remove_saved_university",
    "Remove a university program from the student's saved list.",
    {"properties": {
        "institution_name": {"type": "string"},
        "program_name": {"type": "string"}},
     "required": ["institution_name", "program_name"]},
    saves=True,
)
def remove_saved_university(user_id, institution_name, program_name):
    from utils import database

    return {"removed": bool(database.remove_saved_university(user_id, institution_name, program_name))}
