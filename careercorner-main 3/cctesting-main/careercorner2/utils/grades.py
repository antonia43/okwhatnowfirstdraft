"""Grade helpers for Portuguese admission.

One place for scale conversion, the CIF (admission average) and the comparison
with DGES last-placed grades. No Streamlit calls, so chat functions can use it.

Scales used in the app:
- school subject grades (10th, 11th, 12th): 0-20
- national exam grades, the CIF and DGES last-placed grades: 0-200
"""
import copy
import math

SCALE_20 = 20
SCALE_200 = 200

WEIGHT_PRESETS = {
    "standard": {"secondary": 0.65, "exam": 0.35},
    "equal": {"secondary": 0.50, "exam": 0.50},
    "exam_heavy": {"secondary": 0.40, "exam": 0.60},
    "secondary_heavy": {"secondary": 0.70, "exam": 0.30},
}
DEFAULT_WEIGHTS = WEIGHT_PRESETS["standard"]

# Distance (on the 0-200 scale) from the last-placed grade that counts as "close".
# The grades page always used 1 point on the 0-20 scale, which is 10 here.
CLOSE_MARGIN = 10.0

YEARS = ("10th", "11th", "12th")


# ---- scale conversion -------------------------------------------------------

def guess_scale(value):
    """Grades above 20 can only be on the 0-200 scale."""
    return SCALE_200 if float(value) > SCALE_20 else SCALE_20


def to_200(value, scale=None):
    """Convert a grade to the 0-200 scale. scale is 20 or 200 (guessed if None)."""
    value = float(value)
    scale = scale or guess_scale(value)
    _check_range(value, scale)
    return value * 10 if scale == SCALE_20 else value


def to_20(value, scale=None):
    """Convert a grade to the 0-20 scale. scale is 20 or 200 (guessed if None)."""
    value = float(value)
    scale = scale or guess_scale(value)
    _check_range(value, scale)
    return value / 10 if scale == SCALE_200 else value


def both_scales(value, scale=None):
    """Return the same grade on both scales."""
    return {"on_20": round(to_20(value, scale), 2), "on_200": round(to_200(value, scale), 2)}


def format_grade(value_200, decimals=1):
    """Human text for a grade held on the 0-200 scale, e.g. '138.5/200 (13.85/20)'."""
    v = float(value_200)
    return f"{v:.{decimals}f}/200 ({v / 10:.{decimals + 1}f}/20)"


def _check_range(value, scale):
    if scale not in (SCALE_20, SCALE_200):
        raise ValueError("scale must be 20 or 200")
    if math.isnan(value) or value < 0 or value > scale:
        raise ValueError(f"Grade {value:g} is outside the 0-{scale} scale")


# ---- one saved-grades format ------------------------------------------------

def empty_grades_data():
    return {
        "student_type": "portuguese",
        "track": "",
        "current_year": "",
        "grades": {"10th": {}, "11th": {}, "12th": {}, "exams": {}},
    }


def normalize_grades_data(data):
    """Return a copy with every expected key present; keeps unknown keys."""
    out = empty_grades_data()
    data = copy.deepcopy(data or {})
    grades = data.pop("grades", None) or {}
    out.update(data)
    for key in out["grades"]:
        out["grades"][key] = dict(grades.get(key) or {})
    for key, value in grades.items():
        if key not in out["grades"]:
            out["grades"][key] = value
    return out


def merge_grades_data(existing, update):
    """Merge new grades into saved ones without dropping track or current_year."""
    merged = normalize_grades_data(existing)
    new = normalize_grades_data(update)
    for key in ("student_type", "track", "current_year"):
        if new.get(key):
            merged[key] = new[key]
    for key, subjects in new["grades"].items():
        merged["grades"].setdefault(key, {})
        merged["grades"][key].update(subjects)
    return merged


# ---- averages and CIF -------------------------------------------------------

def secondary_average(grades):
    """Average of all school subject grades above 0, on the 0-20 scale."""
    values = []
    for year in YEARS:
        for subject, grade in (grades.get(year) or {}).items():
            grade = float(grade)
            if grade > 0:
                _check_range(grade, SCALE_20)
                values.append(grade)
    return sum(values) / len(values) if values else 0.0


def exam_average(exams):
    """Average of all exam grades above 0, on the 0-200 scale."""
    values = []
    for subject, grade in (exams or {}).items():
        grade = float(grade)
        if grade > 0:
            _check_range(grade, SCALE_200)
            values.append(grade)
    return sum(values) / len(values) if values else 0.0


def validate_weights(weights):
    w = {"secondary": float(weights["secondary"]), "exam": float(weights["exam"])}
    if w["secondary"] < 0 or w["exam"] < 0 or abs(w["secondary"] + w["exam"] - 1.0) > 0.001:
        raise ValueError("Weights must be positive and add up to 100%")
    return w


def calculate_cif(grades_data, weights=None):
    """Admission average from saved grades.

    weights: a preset name ('standard', 'equal', 'exam_heavy', 'secondary_heavy'),
    a dict {'secondary': 0.6, 'exam': 0.4}, or None for the standard 65/35.
    With no exams yet (or a 10th grader) it is the school average alone.
    """
    data = normalize_grades_data(grades_data)
    secondary_20 = secondary_average(data["grades"])
    exam_200 = exam_average(data["grades"]["exams"])
    secondary_200 = secondary_20 * 10

    if isinstance(weights, str):
        if weights not in WEIGHT_PRESETS:
            raise ValueError(f"Unknown weights '{weights}'. Use one of {sorted(WEIGHT_PRESETS)}")
        weights = WEIGHT_PRESETS[weights]

    if "10th" in (data.get("current_year") or "") or exam_200 == 0:
        used = {"secondary": 1.0, "exam": 0.0}
        cif_200 = secondary_200
        basis = "school grades only (no exam grades yet)"
    else:
        used = validate_weights(weights or DEFAULT_WEIGHTS)
        cif_200 = secondary_200 * used["secondary"] + exam_200 * used["exam"]
        basis = f"{used['secondary']:.0%} school grades + {used['exam']:.0%} exams"

    return {
        "cif_200": round(cif_200, 2),
        "cif_20": round(cif_200 / 10, 2),
        "secondary_average_20": round(secondary_20, 2),
        "exam_average_200": round(exam_200, 2),
        "weights_used": used,
        "basis": basis,
    }


# ---- comparison with DGES last-placed grades --------------------------------

def compare_with_cutoff(student_grade_200, last_placed_200, margin_200=None):
    """Compare a student's grade (0-200) with the last-placed grade (0-200).

    safe   : margin_200 (default 10) or more above last year's cut-off
    target : within margin_200 either way
    reach  : more than margin_200 below
    unknown: no cut-off published
    """
    try:
        cutoff = float(last_placed_200)
    except (TypeError, ValueError):
        cutoff = 0.0
    if math.isnan(cutoff) or cutoff <= 0:
        return {"status": "unknown", "margin_200": None,
                "message": "No last-placed grade is published for this program."}

    close = CLOSE_MARGIN if margin_200 is None else float(margin_200)
    student = float(student_grade_200)
    margin = student - cutoff
    if margin >= close:
        status = "safe"
    elif margin >= -close:
        status = "target"
    else:
        status = "reach"
    return {
        "status": status,
        "margin_200": round(margin, 2),
        "student": both_scales(student, SCALE_200),
        "last_placed": both_scales(cutoff, SCALE_200),
        "message": (f"Your grade {format_grade(student)} vs last placed {format_grade(cutoff)} "
                    f"({margin:+.1f} points on the 0-200 scale). Last year's cut-off is a guide, "
                    f"not a guarantee."),
    }
