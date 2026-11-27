"""Entry requirements of a program for the chat: required entrance exams, minimum grades, and the
student's admission grade computed with that program's own formula (not one average for all).

Data: utils/dges_requirements.py (collected from the DGES course pages).
"""
import re
import unicodedata

from services.chat_functions import chat_function
from services.grade_functions import ENTRIES, _combined, _has_grades
from services.university_functions import find_program, program_from_row
from utils.dges import load_dges_df, normalize_text
from utils.dges_requirements import (admission_for, competition_text, exam_average_needed,
                                     exam_options_text, requirements_for, what_if)
from utils.grades import compare_with_cutoff, secondary_average

# Built-in "what if" scenarios shown when the student is not clearly safe: (label, exam points, school points), 0-200 scale.
SCENARIOS = [("exam grades +10 (1 point out of 20)", 10, 0),
             ("exam grades +20 (2 points out of 20)", 20, 0),
             ("school average +0.5 (out of 20)", 0, 5)]

@chat_function(
    "check_program_requirements",
    "For ONE program, show the entrance exams it requires, the minimum grades, how its admission grade is "
    "weighted, and the student's admission grade for THAT program with their chance (safe, target, reach). "
    "More accurate than check_chances_for_degree because every program weights school grades and exams "
    "differently. Use the course_code and institution_name exactly as returned by search_universities. "
    "Uses the student's saved grades plus any entries given here. Also gives how many points short or above "
    "the last cut-off the student is, the exam average needed to reach it, and ready-made what-if scenarios. "
    "For a different what-if pass exam_boost_200 / school_boost_20. Does not save anything.",
    {"properties": {
        "course_code": {"type": "string", "description": "DGES course code from search_universities"},
        "institution_name": {"type": "string", "description": "Institution name from search_universities"},
        "entries": ENTRIES,
        "exam_boost_200": {"type": "number", "description": "What-if: add this many points (0-200 scale; 10 = 1 point out of 20) to every exam grade. Use when the student asks what happens if they raise an exam grade."},
        "school_boost_20": {"type": "number", "description": "What-if: add this many points (0-20 scale) to the school average."}},
     "required": ["course_code", "institution_name"]},
)
def check_program_requirements(user_id, course_code, institution_name, entries=None,
                               exam_boost_200=None, school_boost_20=None):
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
    cutoff = program["last_grade_200"]
    if cutoff:
        gap = round(result["admission_grade_200"] - cutoff, 1)
        out["points_above_last_cutoff"] = gap if gap >= 0 else 0
        out["points_short_of_last_cutoff"] = round(-gap, 1) if gap < 0 else 0
        if gap < 0:
            need = exam_average_needed(req, school, cutoff)
            out["exam_average_needed_200"] = need if need is not None else "more than 200: exams alone cannot reach it"
    exams = data["grades"].get("exams")
    if (exam_boost_200 or school_boost_20) and exams:
        shifted = what_if(req, school, exams, float(exam_boost_200 or 0), float(school_boost_20 or 0) * 10)
        if shifted["status"] == "ok":
            out["what_if"] = _scenario("your what-if", shifted, cutoff)
    elif out["chance"] != "safe" and exams:
        scenarios = []
        for label, exam_pts, school_pts in SCENARIOS:
            shifted = what_if(req, school, exams, exam_pts, school_pts)
            if shifted["status"] == "ok":
                scenarios.append(_scenario(label, shifted, cutoff))
        out["what_if_scenarios"] = scenarios
    return out

def _scenario(label, result, cutoff):
    """One what-if outcome: the new admission grade and where it lands against the last cut-off."""
    chance = "not_eligible" if not result["meets_minimums"] else (
        compare_with_cutoff(result["admission_grade_200"], cutoff)["status"] if cutoff else "unknown")
    return {"change": label, "admission_grade_200": result["admission_grade_200"], "chance": chance,
            "points_vs_last_cutoff": round(result["admission_grade_200"] - cutoff, 1) if cutoff else None}

def _stems(name):
    text = unicodedata.normalize("NFD", str(name or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    skip = {"engenharia", "ciencias", "licenciatura", "mestrado", "integrado", "curso", "estudos", "tecnologia", "tecnologias"}
    return {w[:6] for w in re.findall(r"[a-z]+", text) if len(w) > 2 and w not in skip}

def _similarity(a, b):
    sa, sb = _stems(a), _stems(b)
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0

@chat_function(
    "find_safer_alternatives",
    "When a program is a reach or the student is below its cut-off, find similar programs (same field of study "
    "or a similar name, same degree level) where the student's admission grade, worked out with each program's "
    "own exams and weights, is safe or on target. Shown on the map. Use the course_code and institution_name of "
    "the program they could not reach, exactly as returned by search_universities. Needs the student's grades. "
    "Does not save anything.",
    {"properties": {
        "course_code": {"type": "string", "description": "DGES course code of the program the student missed"},
        "institution_name": {"type": "string", "description": "Institution name of that program"},
        "region": {"type": "string", "description": "Optional region or city to stay in, e.g. Lisbon"},
        "entries": ENTRIES,
        "limit": {"type": "integer", "description": "How many alternatives (default 6, max 12)"}},
     "required": ["course_code", "institution_name"]},
)
def find_safer_alternatives(user_id, course_code, institution_name, region=None, entries=None, limit=6):
    row = find_program(course_code, institution_name)
    if row is None:
        return {"error": "That program was not found. Search again and use the exact course_code and institution_name."}
    data = _combined(user_id, entries, None, None)
    if not _has_grades(data):
        return {"error": "No grades known yet. Ask the student for their grades first."}
    target = program_from_row(row)
    target_req = requirements_for(course_code, institution_name)
    field = target_req and target_req.get("cnaef")
    school = secondary_average(data["grades"]) * 10
    exams = data["grades"].get("exams")
    wanted_region = normalize_text(region).strip() if region else None
    df = load_dges_df()
    found, missing_exam = [], 0
    for _, r in df.iterrows():
        if str(r.get("course_code")).strip() == str(course_code).strip() and r.get("institution_name") == row.get("institution_name"):
            continue
        if r.get("degree_type") != row.get("degree_type"):
            continue
        if wanted_region and wanted_region not in normalize_text(r.get("region", "")):
            continue
        req = requirements_for(r.get("course_code"), r.get("institution_name"))
        if req is None:
            continue
        similar = _similarity(target["program_name"], r.get("course_name"))
        same_field = bool(field) and req.get("cnaef") == field
        if not (same_field or similar >= 0.5):
            continue
        result = admission_for(req, school, exams)
        if result["status"] == "needs_exam":
            missing_exam += 1
            continue
        if result["status"] != "ok" or not result["meets_minimums"]:
            continue
        program = program_from_row(r, result["admission_grade_200"])
        if program["chance"] not in ("safe", "target") or not program["last_grade_200"]:
            continue
        program["your_admission_grade_200"] = result["admission_grade_200"]
        program["points_above_last_cutoff"] = round(result["admission_grade_200"] - program["last_grade_200"], 1)
        program["similarity"] = round(similar + (0.5 if same_field else 0), 2)
        program["why_similar"] = ("same field of study (" + (req.get("field") or "") + ")" if same_field else "similar name")
        found.append(program)
    found.sort(key=lambda p: (p["chance"] != "safe", -p["similarity"], -p["last_grade_200"]))
    limit = max(1, min(int(limit or 6), 12))
    shown = found[:limit]
    out = {"missed_program": {"program_name": target["program_name"], "institution_name": target["institution_name"],
                              "last_grade_200": target["last_grade_200"]},
           "alternatives_found": len(found), "shown": len(shown), "total_found": len(found),
           "without_map_pin": sum(1 for p in shown if p["coordinates"] is None),
           "grade_used_200": None, "universities": shown, "display": "map",
           "note": "Chance is worked out with each program's own exams and weights. Similar means the same DGES field or a similar name; check the content of each degree."}
    if missing_exam:
        out["skipped_because_exam_missing"] = missing_exam
    if not shown:
        out["message"] = "No safe or target alternatives found with these grades" + (f" in {region}" if region else "") + ". Try another region, or ask whether they have another exam grade."
    return out
