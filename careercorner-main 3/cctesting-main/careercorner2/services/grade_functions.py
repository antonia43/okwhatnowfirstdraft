"""Grade abilities for the chat. They wrap services/grade_tools.py.

Grades reach the chat as a list of entries (name, grade, period) so Gemini can
fill them in from a screenshot or from what the student types. A student who
is logged in keeps their grades in their profile; a guest's grades only live in
the conversation, so a guest passes them in every time.
"""
from services.chat_functions import chat_function, is_guest
from services import grade_tools
from utils.grades import (
    SCALE_20,
    SCALE_200,
    calculate_cif,
    merge_grades_data,
    normalize_grades_data,
)

PERIODS = ("10th", "11th", "12th", "exam")
WEIGHT_NAMES = ("standard", "equal", "exam_heavy", "secondary_heavy")

ENTRIES = {
    "type": "array",
    "description": "Grades as a list. School subject grades are 0-20, national exam grades 0-200.",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Subject or exam, e.g. 'Matemática A' or 'Matemática A (635)'"},
            "grade": {"type": "number", "description": "0-20 for school subjects, 0-200 for exams"},
            "period": {"type": "string", "enum": list(PERIODS),
                       "description": "'10th', '11th', '12th' for school grades, 'exam' for a national exam"},
        },
        "required": ["name", "grade", "period"],
    },
}
CURRENT_YEAR = {
    "type": "string",
    "description": "'10th Grade', '11th Grade', '12th Grade (In Progress)' or '12th Grade (Completed)'",
}
WEIGHTS = {
    "type": "string",
    "enum": list(WEIGHT_NAMES),
    "description": "How school grades and exams are weighted: standard 65/35 (default), equal 50/50, "
                   "exam_heavy 40/60, secondary_heavy 70/30",
}


def entries_to_grades_data(entries, current_year=None, track=None):
    """Turn the chat's list of grade entries into the saved-grades structure."""
    data = {"grades": {"10th": {}, "11th": {}, "12th": {}, "exams": {}}}
    if current_year:
        data["current_year"] = current_year
    if track:
        data["track"] = track
    for entry in entries or []:
        name, grade, period = str(entry["name"]).strip(), float(entry["grade"]), entry["period"]
        if period not in PERIODS:
            raise ValueError(f"Unknown period '{period}' for {name}. Use one of {', '.join(PERIODS)}.")
        scale = SCALE_200 if period == "exam" else SCALE_20
        if not 0 <= grade <= scale:
            raise ValueError(f"{name}: {grade:g} is outside the 0-{scale} scale for {period} grades.")
        data["grades"]["exams" if period == "exam" else period][name] = grade
    return data


def _stored(user_id):
    """Grades saved in the student's profile, if any."""
    if is_guest(user_id):
        return normalize_grades_data(None)
    from utils import database

    return normalize_grades_data(database.load_student_profile(user_id).get("grades_data"))


def _combined(user_id, entries, current_year, track):
    return merge_grades_data(_stored(user_id), entries_to_grades_data(entries, current_year, track))


def _cif_summary(grades_data, weights):
    cif = calculate_cif(grades_data, weights)
    cif["note"] = ("This is the admission average from school and exam grades. The real admission grade "
                   "can weigh things differently for each degree.")
    return cif


def _has_grades(data):
    return any(data["grades"].get(k) for k in data["grades"])


@chat_function(
    "calculate_admission_grade",
    "Calculate the student's admission average (CIF) from grades. Uses their saved grades plus any "
    "grades given here. Does not save anything.",
    {"properties": {"entries": ENTRIES, "current_year": CURRENT_YEAR, "weights": WEIGHTS}},
)
def calculate_admission_grade(user_id, entries=None, current_year=None, weights=None):
    data = _combined(user_id, entries, current_year, None)
    if not _has_grades(data):
        return {"error": "No grades yet. Ask the student for their grades or a screenshot of them."}
    return _cif_summary(data, weights)


@chat_function(
    "save_grades",
    "Save the student's grades to their account (adds to or corrects what was saved) and return the "
    "admission average. Only call after the student has confirmed the grades are right.",
    {"properties": {"entries": ENTRIES, "current_year": CURRENT_YEAR,
                    "track": {"type": "string", "description": "e.g. 'Ciências e Tecnologias'"}},
     "required": ["entries"]},
    saves=True,
)
def save_grades(user_id, entries, current_year=None, track=None):
    from utils import database

    data = _combined(user_id, entries, current_year, track)
    profile = database.load_student_profile(user_id)
    profile["grades_data"] = data
    if not database.save_student_profile(user_id, profile):
        raise RuntimeError("Could not save the grades")
    return {"saved": True, "grades_data": data, **_cif_summary(data, None)}


@chat_function(
    "get_saved_grades",
    "Read the grades saved in the student's account, with their admission average.",
)
def get_saved_grades(user_id):
    data = _stored(user_id)
    if not _has_grades(data):
        return {"has_grades": False}
    return {"has_grades": True, "grades_data": data, **_cif_summary(data, None)}


def _grade_to_use(user_id, grade_200):
    if grade_200 is not None:
        return float(grade_200)
    data = _stored(user_id)
    return calculate_cif(data)["cif_200"] if _has_grades(data) else None


@chat_function(
    "check_chances_for_degree",
    "Show the range of last-placed grades (0-200) for a degree in Portugal and where the student's grade "
    "sits. Works without a grade (range only). Uses the saved admission average unless a grade is given.",
    {"properties": {
        "degree_name": {"type": "string", "description": "Degree name, e.g. 'Engenharia Informática'"},
        "grade_200": {"type": "number", "description": "Student's grade on the 0-200 scale, if known"}},
     "required": ["degree_name"]},
)
def check_chances_for_degree(user_id, degree_name, grade_200=None):
    return grade_tools.check_course_grade_range(degree_name, _grade_to_use(user_id, grade_200))


@chat_function(
    "compare_saved_universities",
    "Compare the student's saved universities with their grade: safe, target or reach for each. "
    "Uses the saved admission average unless a grade is given.",
    {"properties": {"grade_200": {"type": "number", "description": "Student's grade on the 0-200 scale, if known"}}},
)
def compare_saved_universities(user_id, grade_200=None):
    grade = _grade_to_use(user_id, grade_200)
    if grade is None:
        return {"error": "No grade known yet. Ask for the student's grades first."}
    return grade_tools.compare_with_saved_universities(user_id, grade)


def grades_to_entries(grades):
    """Flatten the transcript structure {'10th': {name: grade}, ..., 'exams': {...}} into chat entries.

    Returns (entries, skipped) where skipped lists anything that was not a usable number.
    """
    entries, skipped = [], []
    for period, subjects in (grades or {}).items():
        key = "exam" if period == "exams" else period
        if key not in PERIODS or not isinstance(subjects, dict):
            continue
        for name, value in subjects.items():
            try:
                grade = float(value)
            except (TypeError, ValueError):
                skipped.append(f"{name} ({key}): {value}")
                continue
            scale = SCALE_200 if key == "exam" else SCALE_20
            if not 0 <= grade <= scale:
                skipped.append(f"{name} ({key}): {value}")
                continue
            entries.append({"name": str(name).strip(), "grade": grade, "period": key})
    return entries, skipped


@chat_function(
    "read_uploaded_grades",
    "Read the grades from the screenshot or PDF the student just uploaded (a Portuguese school transcript). "
    "Nothing is calculated or saved. Show the student what was read and ask them to check it, then use "
    "calculate_admission_grade or save_grades with the corrected entries.",
    uses_session=True,
)
def read_uploaded_grades(user_id, session):
    upload = (session or {}).get("upload")
    if not upload:
        return {"error": "No file has been uploaded. Ask the student to attach a screenshot or PDF of their grades."}
    data = grade_tools.extract_grades_from_file(upload["bytes"], upload["mime"], "portuguese", user_id=user_id)
    if data.get("student_type") != "portuguese":
        return {"error": "This looks like a non-Portuguese transcript. Grades from other countries are not supported yet."}
    entries, skipped = grades_to_entries(data.get("grades"))
    if not entries:
        return {"error": "No grades could be read from this file. Ask for a clearer picture or the grades typed in."}
    return {"entries": entries, "count": len(entries), "skipped": skipped,
            "current_year": data.get("current_year"), "track": data.get("track")}
