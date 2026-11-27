"""Entry requirements of a program for the chat: required entrance exams, minimum grades, and the
student's admission grade computed with that program's own formula (not one average for all).

Data: utils/dges_requirements.py (collected from the DGES course pages).
"""
from services.chat_functions import chat_function
from services.grade_functions import ENTRIES, _combined, _has_grades
from services.university_functions import find_program, program_from_row
from utils.dges_requirements import (admission_for, competition_text, exam_options_text,
                                     requirements_for)
from utils.grades import compare_with_cutoff, secondary_average

@chat_function(
    "check_program_requirements",
    "For ONE program, show the entrance exams it requires, the minimum grades, how its admission grade is "
    "weighted, and the student's admission grade for THAT program with their chance (safe, target, reach). "
    "More accurate than check_chances_for_degree because every program weights school grades and exams "
    "differently. Use the course_code and institution_name exactly as returned by search_universities. "
    "Uses the student's saved grades plus any entries given here. Does not save anything.",
    {"properties": {
        "course_code": {"type": "string", "description": "DGES course code from search_universities"},
        "institution_name": {"type": "string", "description": "Institution name from search_universities"},
        "entries": ENTRIES},
     "required": ["course_code", "institution_name"]},
)
def check_program_requirements(user_id, course_code, institution_name, entries=None):
    row = find_program(course_code, institution_name)
    if row is None:
        return {"error": "That program was not found. Search again and use the exact course_code and institution_name."}
    program = program_from_row(row)
    req = requirements_for(course_code, institution_name)
    out = {"program_name": program["program_name"], "institution_name": program["institution_name"],
           "last_grade_2026": program["last_grade_200"], "last_grade_2025": program["previous_grade_200"],
           "trend": program["trend"]}
    if req is None:
        out["message"] = ("The entry requirements for this program are not available here. "
                          "Point the student to the DGES course page.")
        return out
    out.update({"entrance_exams": exam_options_text(req),
                "formula": f"{req['w_secondary']:g}% school average + {req['w_exams']:g}% entrance exams",
                "minimum_admission_grade": req["min_application"], "minimum_exam_average": req["min_exams"],
                "last_grade_2024": req["last_grade_2024"], "last_grade_2023": req["last_grade_2023"],
                "competition": competition_text(req)})
    data = _combined(user_id, entries, None, None)
    if not _has_grades(data):
        out["message"] = "No grades known yet, so this shows the requirements only."
        return out
    school = secondary_average(data["grades"]) * 10
    result = admission_for(req, school, data["grades"].get("exams"))
    if result["status"] == "needs_exam":
        out["needs_exam"] = result["exams_needed"]
        out["school_average_200"] = round(school, 1)
        out["message"] = "Ask the student for their grade in one of the accepted exams to see their chance."
        return out
    out.update({k: result[k] for k in ("admission_grade_200", "exams_used", "exam_average_200", "meets_minimums", "problems")})
    comparison = compare_with_cutoff(result["admission_grade_200"], program["last_grade_200"])
    out["chance"] = "not_eligible" if not result["meets_minimums"] else comparison["status"]
    out["margin_200"] = comparison["margin_200"]
    return out
