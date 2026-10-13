"""Structured access to what a student saved: degrees and universities.

Degree names are stored as a list when a degree report is saved. Saved
universities carry a numeric last-placed grade. Old records that only have
text are still read, so nothing a student saved earlier is lost.
"""
import re

from utils.grades import compare_with_cutoff

_DEGREE_HEADING = re.compile(r"###\s*\d+\.\s*([^(]+?)\s*\(")
_LEADING_NUMBER = re.compile(r"\s*([0-9]+(?:\.[0-9]+)?)")
_ORDER = {"safe": 0, "target": 1, "reach": 2, "unknown": 3}


def extract_degree_names(markdown):
    """Degree names from a degree report ('### 1. Name (' headings)."""
    names = [d.strip() for d in _DEGREE_HEADING.findall(markdown or "")]
    return [n for n in names if len(n) > 3]


def get_saved_degrees(user_id):
    """Degree names from the student's newest degree report that has any."""
    from utils.database import load_reports  # imported late: it opens the database

    for report in load_reports(user_id, "degree"):  # newest first
        degrees = (report.get("cv_data") or {}).get("degrees") or extract_degree_names(
            report.get("content", "")
        )
        if degrees:
            return degrees
    return []


def university_grade_200(uni):
    """Last-placed grade of a saved university on the 0-200 scale, or None."""
    value = uni.get("last_grade_200")
    if value is not None:
        return float(value)
    match = _LEADING_NUMBER.match(str(uni.get("average_grade_required") or ""))
    if not match:
        return None
    number = float(match.group(1))
    # Old records stored a 0-200 number with a "/20" label.
    return number * 10 if number <= 20 else number


def compare_universities(universities, student_grade_200):
    """Label each university safe, target, reach or unknown for this grade."""
    results = []
    for uni in universities:
        cutoff = university_grade_200(uni)
        comparison = compare_with_cutoff(student_grade_200, cutoff)
        results.append({
            "name": uni.get("name", ""),
            "program_name": uni.get("program_name", ""),
            "location": uni.get("location", ""),
            "last_grade_200": cutoff,
            **comparison,
        })
    results.sort(key=lambda r: (_ORDER[r["status"]], -(r["margin_200"] or 0)))
    return results


def compare_saved_universities(user_id, student_grade_200):
    """Compare the student's saved universities with their grade (0-200)."""
    from utils.database import get_saved_universities

    return compare_universities(get_saved_universities(user_id), student_grade_200)
