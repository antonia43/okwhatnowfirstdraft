"""Grade functions for the chat and the pages. No Streamlit calls.

Each function does what the Grades Analysis page did before, so the page and
the chat give the same answers:
- calculate_admission_average / calculate_and_save_grade : the CIF (0-200)
- generate_grade_report                                   : the saved markdown summary
- save_international_grades                               : store grades without a calculation
- check_course_grade_range                                : min / max / position against DGES
- compare_with_saved_universities                         : safe / target / reach per saved university
- extract_grades_from_file                                : read a transcript with Gemini
- generate_international_overview                         : AI overview for international students

Grades: school subjects are 0-20, exams, the CIF and DGES last-placed grades are 0-200.
"""
import json
import os
from datetime import datetime

from utils.dges import find_programs
from utils.grades import (
    calculate_cif,
    normalize_grades_data,
)

GRADES_MODEL_NAME = "gemini-2.5-flash"
DEFAULT_YEAR = "12th Grade (Completed)"
YEARS = ("10th", "11th", "12th")


class GradeExtractionError(Exception):
    """The transcript could not be read or the AI answer was not valid JSON."""


def is_guest(user_id):
    return not user_id or str(user_id).startswith("guest-")


# ---- the CIF ----------------------------------------------------------------

def _grades_data(grades_data):
    """Saved grades with the year defaulted the way the page defaulted it."""
    data = normalize_grades_data(grades_data)
    if not data.get("current_year"):
        data["current_year"] = DEFAULT_YEAR
    return data


def calculate_admission_average(grades_data, weights=None):
    """Portuguese admission average (CIF) on the 0-200 scale.

    weights: None (65/35), a preset name, or {'secondary': 0.6, 'exam': 0.4}.
    10th graders and students with no exam grades get school grades only.
    """
    return calculate_cif(_grades_data(grades_data), weights)["cif_200"]


def generate_grade_report(grades_data, final_grade, weights):
    """The markdown summary saved with a grades report."""
    data = _grades_data(grades_data)
    grades = data["grades"]
    current_year = data["current_year"]

    if weights["exam"] == 0:
        calc_method = "100% Secondary School Grades (No exams yet)"
    else:
        calc_method = f"{int(round(weights['secondary'] * 100))}% Secondary + {int(round(weights['exam'] * 100))}% Exams"

    report = f"""# Grades Analysis Report

## Final Admission Average
**CIF Score:** {final_grade:.2f}

**Current Year:** {current_year}
**Calculation Method:** {calc_method}

## Grade Breakdown

### Secondary School Grades (10th-12th)
"""
    for year in YEARS:
        year_grades = grades.get(year, {})
        if year_grades:
            valid = [g for g in year_grades.values() if g > 0]
            if valid:
                report += f"\n**{year} Grade:** {sum(valid) / len(valid):.2f}\n"
                for subject, grade in year_grades.items():
                    if grade > 0:
                        report += f" - {subject}: {grade}\n"
        else:
            report += f"\n**{year} Grade:** No grades entered yet\n"

    report += "\n### National Exams\n"
    exams = grades.get("exams", {})
    if exams and any(score > 0 for score in exams.values()):
        for exam, grade in exams.items():
            if grade > 0:
                report += f"- {exam}: {grade}\n"
    elif "10th" in current_year:
        report += "*No exams - 10th grade student*\n"
    else:
        report += "*No exams recorded yet*\n"

    report += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    return report


def calculate_and_save_grade(user_id, grades_data, weights=None, save=True):
    """Calculate the CIF and, for signed-in students, save it as a grades report.

    Returns the numbers plus 'saved' (bool) and 'report_id'. Guests are never saved.
    """
    data = _grades_data(grades_data)
    result = calculate_cif(data, weights)
    used = result["weights_used"]
    final = result["cif_200"]
    out = dict(result, saved=False, report_id=None)
    out["summary"] = generate_grade_report(data, final, used)

    if save and not is_guest(user_id):
        from utils.database import save_report  # late import: it opens the database

        out["report_id"] = save_report(
            user_id=user_id,
            report_type="grades",
            title=f"Grades - CIF {final:.1f}/200 ({final / 10:.2f}/20) - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=json.dumps({
                "student_grades_data": data,
                "final_cif": float(final),
                "weights_used": used,
                "summary": out["summary"],
            }),
            cv_data=None,
        )
        out["saved"] = out["report_id"] is not None
    return out


def save_international_grades(user_id, grades_data):
    """Store an international student's grades without a calculation."""
    country = grades_data.get("country", "International")
    out = {"saved": False, "report_id": None, "subjects": len(grades_data.get("subjects", []))}
    if is_guest(user_id):
        return out
    from utils.database import save_report

    out["report_id"] = save_report(
        user_id=user_id,
        report_type="grades",
        title=f"International Grades - {country} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=json.dumps({
            "student_type": "international",
            "grades_data": grades_data,
            "saved_at": datetime.now().isoformat(),
        }),
        cv_data=None,
    )
    out["saved"] = out["report_id"] is not None
    return out


# ---- comparing with DGES ------------------------------------------------------

def check_course_grade_range(course_name, student_grade_200, df=None):
    """Where a grade sits among the last-placed grades of every program with this course name."""
    programs = find_programs(course_name, df)
    if programs.empty:
        return {"found": 0, "message": f"No programs found for '{course_name}'. Try a different name."}

    grades = [float(g) for g in programs["last_grade"].dropna() if float(g) > 0] \
        if "last_grade" in programs.columns else []
    if not grades:
        return {"found": len(programs), "message": "No valid entry grades found for this course."}

    low, high, avg = min(grades), max(grades), sum(grades) / len(grades)
    if student_grade_200 is None:  # no grade known yet: just the range
        return {"found": len(programs), "course_name": course_name, "lowest_entry": low,
                "highest_entry": high, "average_entry": avg,
                "message": "No grade known yet, so this is only the range of last-placed grades."}
    student = float(student_grade_200)

    if student < low:
        status, position = "Below minimum - Need to improve", 0.0
    elif student >= high:
        status, position = "Excellent - Competitive everywhere!", 100.0
    else:
        position = (student - low) / (high - low) * 100
        if position >= 75:
            status = "Strong - Good chances at most programs"
        elif position >= 50:
            status = "Moderate - Competitive for many programs"
        else:
            status = "Borderline - Limited options"

    return {
        "found": len(programs),
        "course_name": course_name,
        "student_grade": student,
        "lowest_entry": low,
        "highest_entry": high,
        "average_entry": avg,
        "above_minimum": student >= low,
        "points_needed_for_minimum": max(0.0, low - student),
        "competitive_everywhere": student >= high,
        "above_average": student >= avg,
        "position_percent": position,
        "status": status,
    }


def compare_with_saved_universities(user_id, student_grade_200, margin_200=None):
    """Safe / target / reach for each of the student's saved universities."""
    from utils.saved_data import compare_saved_universities

    results = compare_saved_universities(user_id, student_grade_200)
    if margin_200 is not None:
        from utils.grades import compare_with_cutoff
        for r in results:
            r.update(compare_with_cutoff(student_grade_200, r["last_grade_200"], margin_200))
    return results


# ---- reading a transcript with Gemini -----------------------------------------

PORTUGUESE_PROMPT = """Analyze this PORTUGUESE student transcript and extract ALL grades.
Return ONLY valid JSON in this exact format:
{
  "student_type": "portuguese",
  "current_year": "10th Grade / 11th Grade / 12th Grade (In Progress) / 12th Grade (Completed)",
  "track": "Ciências e Tecnologias / Ciências Socioeconómicas / Línguas e Humanidades / Artes Visuais",
  "grades": {
    "10th": {"Português": 15, "Matemática A": 17, "Inglês": 16, ...},
    "11th": {"Português": 16, "Física e Química A": 18, ...},
    "12th": {"Português": 17, ...},
    "exams": {"Português (639)": 150, "Matemática A (635)": 170, ...}
  }
}

Rules:
- Extract ALL visible subjects and grades
- Grades are 0-20 scale for subjects, 0-200 for exams
- If year or track unclear, make best guess
- Return ONLY JSON, no explanations"""

INTERNATIONAL_PROMPT = """Analyze this INTERNATIONAL student transcript and extract ALL grades.
Return ONLY valid JSON in this exact format:
{
  "student_type": "international",
  "country": "country name or Unknown",
  "grade_scale": "e.g., 0-100, A-F, 1-5",
  "subjects": [
    {"name": "Mathematics", "grade": "95", "year": "11th Grade"},
    {"name": "Physics", "grade": "A", "year": "12th Grade"},
    {"name": "Chemistry", "grade": "4.0", "year": "10th Grade"}
  ],
  "current_year": "best guess of student's current year",
  "school_type": "if visible (IB, A-Levels, etc.)"
}

Rules:
- Extract ALL visible subjects with their exact grades
- Keep grade format as shown (numbers, letters, GPA)
- If year not shown, use "N/A"
- Return ONLY JSON, no explanations"""


def _default_model():
    """Gemini wrapper, created only when needed so the app boots without a key."""
    from services.langfuse_helper import LangfuseGeminiWrapper
    from utils.gemini_key import get_gemini_api_key

    return LangfuseGeminiWrapper(api_key=get_gemini_api_key(), model=GRADES_MODEL_NAME)


def parse_extraction(text):
    """Turn Gemini's JSON answer into the saved-grades structure."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise GradeExtractionError(f"Could not parse AI response: {e}") from e

    if data.get("student_type") == "portuguese":
        return {
            "student_type": "portuguese",
            "current_year": data.get("current_year", DEFAULT_YEAR),
            "track": data.get("track", "Ciências e Tecnologias"),
            "grades": data.get("grades", {}),
            "input_method": "upload",
        }
    return {
        "student_type": "international",
        "input_method": "upload",
        "country": data.get("country", "Unknown"),
        "grade_scale": data.get("grade_scale", "Unknown"),
        "subjects": data.get("subjects", []),
        "current_year": data.get("current_year", ""),
        "school_type": data.get("school_type", ""),
    }


def extract_grades_from_file(file_bytes, mime_type, student_type="portuguese",
                             user_id=None, session_id=None, model=None):
    """Read grades from a transcript image or PDF with Gemini (multimodal)."""
    prompt = PORTUGUESE_PROMPT if student_type == "portuguese" else INTERNATIONAL_PROMPT
    model = model or _default_model()
    try:
        raw = model.generate_content_multimodal(
            prompt=prompt,
            file_data=file_bytes,
            mime_type=mime_type,
            user_id=user_id,
            session_id=session_id,
            temperature=0.1,
            metadata={"type": "grades_extraction"},
        )
    except Exception as e:
        raise GradeExtractionError(f"Error extracting grades: {e}") from e
    return parse_extraction(raw)


# ---- international overview -----------------------------------------------------

def build_international_overview_prompt(grades_data):
    subjects = grades_data.get("subjects", [])
    country = grades_data.get("country", "International")
    grade_scale = grades_data.get("grade_scale", "Unknown")
    subjects_text = "\n".join(
        f"- {s['name']}: {s['grade']} ({s.get('year', 'N/A')})" for s in subjects
    )
    return f"""Analyze this international student's academic profile and provide insights.

**Student Profile:**
- Country: {country}
- Grade Scale: {grade_scale}
- Total Subjects: {len(subjects)}

**Grades:**
{subjects_text}

**Provide a structured analysis:**

## Academic Strengths
[Identify 3-4 subjects where the student excels and what this indicates about their skills]

## Areas for Improvement
[Identify 2-3 subjects that could be improved and provide constructive advice]

## Recommended Degree Paths
[Based on their grades, suggest 4-5 specific degree programs they would be well-suited for. Be specific with degree names.]

## Study Tips
[2-3 actionable tips to improve in weaker areas]

---

**FORMATTING RULES:**
- Use markdown headers (##) and bullet points
- Be encouraging and constructive
- Focus on specific, actionable insights
- Suggest degrees that match their strongest subjects
- Keep it concise (under 400 words total)
"""


def generate_international_overview(grades_data, user_id=None, session_id=None, model=None):
    """AI overview of an international student's strengths and degree ideas."""
    model = model or _default_model()
    return model.generate_content(
        prompt=build_international_overview_prompt(grades_data),
        user_id=user_id,
        session_id=session_id,
        temperature=0.7,
        metadata={"type": "international_grades_overview"},
    )
