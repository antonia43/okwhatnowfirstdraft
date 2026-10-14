"""What the assistant knows about the student, and a way to add to it.

get_student_profile reads everything the student has saved (grades, quiz results, universities)
plus a few things they told the chat (year, track, interests, preferred regions, notes).
Guests have nothing stored, so they get an empty profile and cannot save details.
"""
import json

from services.chat_functions import chat_function, is_guest

ABOUT_FIELDS = {
    "school_year": "10th, 11th, 12th, finished school, ...",
    "track": "Their school track or course, e.g. Sciences and Technology",
    "interests": "Subjects, hobbies or topics they like",
    "preferred_regions": "Where in Portugal they would like to study",
    "notes": "Anything else worth remembering about their plans",
}


def _db():
    from utils import database

    return database


def _about(user_id):
    about = _db().load_student_profile(user_id).get("about")
    return about if isinstance(about, dict) else {}


def _latest(reports):
    return reports[0] if reports else None


def _cv(report):
    data = report.get("cv_data") if report else None
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            data = None
    return data if isinstance(data, dict) else {}


@chat_function(
    "get_student_profile",
    "What is already known about the student: whether they have saved grades and their admission average, "
    "their latest career quiz sectors and degree quiz picks, saved universities, and details they shared "
    "(school year, track, interests, preferred regions). Use it to skip questions they already answered.",
)
def get_student_profile(user_id):
    if is_guest(user_id):
        return {"signed_in": False, "note": "Guest: nothing is stored. Details only last for this chat."}
    from services.grade_functions import _cif_summary, _has_grades, _stored

    db = _db()
    grades = _stored(user_id)
    sector = _cv(_latest(db.load_reports(user_id, "career_quiz")))
    degree = _cv(_latest(db.load_reports(user_id, "degree")))
    unis = db.get_saved_universities(user_id) or []
    profile = {
        "signed_in": True,
        "has_grades": _has_grades(grades),
        "sector_quiz": ({"sectors": sector.get("recommended_sectors"),
                         "top_sector": sector.get("recommended_sector")} if sector else None),
        "degree_quiz": ({"field": degree.get("field"), "top_degrees": degree.get("degrees")} if degree else None),
        "saved_universities_count": len(unis),
        "about": _about(user_id),
    }
    if profile["has_grades"]:
        profile["admission_average"] = _cif_summary(grades, None)
    return profile


@chat_function(
    "update_student_profile",
    "Remember details the student shares so they don't have to repeat them. Only send what they said. "
    "Fields: " + "; ".join(f"{k} ({v})" for k, v in ABOUT_FIELDS.items()) + ". Send an empty string to clear a field.",
    {"properties": {k: {"type": "string", "description": v} for k, v in ABOUT_FIELDS.items()}},
    saves=True,
)
def update_student_profile(user_id, **fields):
    updates = {k: str(v).strip() for k, v in fields.items() if k in ABOUT_FIELDS and v is not None}
    if not updates:
        raise ValueError("No profile details were given")
    db = _db()
    profile = db.load_student_profile(user_id)
    about = profile.get("about") if isinstance(profile.get("about"), dict) else {}
    for key, value in updates.items():
        if value:
            about[key] = value
        else:
            about.pop(key, None)
    profile["about"] = about
    if not db.save_student_profile(user_id, profile):
        raise RuntimeError("Could not save the profile")
    return {"saved": True, "about": about}
