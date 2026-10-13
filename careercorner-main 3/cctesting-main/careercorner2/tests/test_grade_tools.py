import json

import pandas as pd
import pytest

from services import grade_tools as gt


def old_calculate_admission_average(grades_data, weights):
    """The page's original calculation, copied unchanged, for comparison."""
    grades = grades_data.get("grades", {})
    current_year = grades_data.get("current_year", "12th Grade (Completed)")
    all_grades = []
    for year in ["10th", "11th", "12th"]:
        all_grades.extend([g for g in grades.get(year, {}).values() if g > 0])
    secondary_avg = sum(all_grades) / len(all_grades) if all_grades else 0
    exams = grades.get("exams", {})
    exam_avg = sum(exams.values()) / len(exams) if exams else 0
    secondary_200 = secondary_avg * 10
    if "10th" in current_year:
        return secondary_200
    if exam_avg > 0:
        return secondary_200 * weights["secondary"] + exam_avg * weights["exam"]
    return secondary_200


def student(year="12th Grade (Completed)"):
    return {
        "current_year": year,
        "track": "Ciências e Tecnologias",
        "grades": {
            "10th": {"Português": 15, "Matemática A": 17, "Inglês": 16},
            "11th": {"Português": 16, "Matemática A": 18, "Inglês": 15},
            "12th": {"Português": 17, "Matemática A": 19},
            "exams": {"Português (639)": 150, "Matemática A (635)": 170},
        },
    }


PRESETS = {
    "standard": {"secondary": 0.65, "exam": 0.35},
    "equal": {"secondary": 0.5, "exam": 0.5},
    "exam_heavy": {"secondary": 0.4, "exam": 0.6},
    "secondary_heavy": {"secondary": 0.7, "exam": 0.3},
}


@pytest.mark.parametrize("year", ["10th Grade", "11th Grade", "12th Grade (In Progress)", "12th Grade (Completed)"])
@pytest.mark.parametrize("name", PRESETS)
def test_same_cif_as_the_old_page(year, name):
    data = student(year)
    assert gt.calculate_admission_average(data, name) == pytest.approx(
        old_calculate_admission_average(data, PRESETS[name]), abs=0.01)


def test_custom_weights_and_default():
    data = student()
    assert gt.calculate_admission_average(data, {"secondary": 0.6, "exam": 0.4}) == pytest.approx(
        old_calculate_admission_average(data, {"secondary": 0.6, "exam": 0.4}), abs=0.01)
    assert gt.calculate_admission_average(data) == pytest.approx(
        old_calculate_admission_average(data, PRESETS["standard"]), abs=0.01)


def test_no_exams_uses_school_grades_only():
    data = student()
    data["grades"]["exams"] = {}
    assert gt.calculate_admission_average(data, "equal") == pytest.approx(
        old_calculate_admission_average(data, PRESETS["equal"]), abs=0.01)


def test_missing_year_defaults_like_the_old_page_but_10th_is_kept():
    data = student()
    del data["current_year"]
    assert gt.calculate_admission_average(data) == pytest.approx(
        old_calculate_admission_average(data, PRESETS["standard"]), abs=0.01)
    tenth = student("10th Grade")
    secondary_only = sum([15, 17, 16, 16, 18, 15, 17, 19]) / 8 * 10
    assert gt.calculate_admission_average(tenth, "equal") == pytest.approx(secondary_only, abs=0.01)


def test_report_text_matches_the_old_format():
    data = student("11th Grade")
    text = gt.generate_grade_report(data, 160.5, PRESETS["standard"])
    assert text.startswith("# Grades Analysis Report\n\n## Final Admission Average\n**CIF Score:** 160.50")
    assert "**Calculation Method:** 65% Secondary + 35% Exams" in text
    assert "**10th Grade:** 16.00\n - Português: 15" in text
    assert "- Matemática A (635): 170" in text
    none = gt.generate_grade_report({"current_year": "10th Grade", "grades": {}}, 0, {"secondary": 1.0, "exam": 0.0})
    assert "100% Secondary School Grades (No exams yet)" in none
    assert "*No exams - 10th grade student*" in none
    assert "**11th Grade:** No grades entered yet" in none


class FakeDb:
    def __init__(self, monkeypatch):
        self.saved = []
        import sys, types
        mod = types.ModuleType("utils.database")
        mod.save_report = lambda **kw: self.saved.append(kw) or len(self.saved)
        monkeypatch.setitem(sys.modules, "utils.database", mod)


def test_save_uses_the_old_title_and_content(monkeypatch):
    db = FakeDb(monkeypatch)
    out = gt.calculate_and_save_grade("ana@x.com", student(), "standard")
    assert out["saved"] and out["report_id"] == 1
    kw = db.saved[0]
    assert kw["report_type"] == "grades" and kw["cv_data"] is None and kw["user_id"] == "ana@x.com"
    assert kw["title"].startswith(f"Grades - CIF {out['cif_200']:.1f}/200 ({out['cif_200'] / 10:.2f}/20) - ")
    content = json.loads(kw["content"])
    assert set(content) == {"student_grades_data", "final_cif", "weights_used", "summary"}
    assert content["weights_used"] == PRESETS["standard"]


def test_guests_are_never_saved(monkeypatch):
    db = FakeDb(monkeypatch)
    out = gt.calculate_and_save_grade("guest-ab12cd34", student(), "standard")
    assert not out["saved"] and db.saved == [] and out["cif_200"] > 0
    assert not gt.save_international_grades("guest-ab12cd34", {"subjects": []})["saved"]


def test_international_save_format(monkeypatch):
    db = FakeDb(monkeypatch)
    data = {"country": "UK", "grade_scale": "A-F", "subjects": [{"name": "Maths", "grade": "A", "year": "12th"}]}
    gt.save_international_grades("ana@x.com", data)
    kw = db.saved[0]
    assert kw["title"].startswith("International Grades - UK - ")
    content = json.loads(kw["content"])
    assert content["student_type"] == "international" and content["grades_data"] == data and "saved_at" in content


DF = pd.DataFrame({
    "course_code": ["1", "2", "3", "4"],
    "institution_name": ["A", "B", "C", "D"],
    "course_name": ["Medicina", "Medicina", "Engenharia Informática", "Medicina Dentária"],
    "last_grade": [180.0, 160.0, 150.0, 0.0],
})


def test_course_range_like_the_old_page():
    r = gt.check_course_grade_range("medicina", 170, DF)
    assert r["found"] == 3 and r["lowest_entry"] == 160 and r["highest_entry"] == 180
    assert r["above_minimum"] and not r["competitive_everywhere"]
    assert r["position_percent"] == pytest.approx(50) and r["status"].startswith("Moderate")
    assert gt.check_course_grade_range("Medicina", 150, DF)["status"].startswith("Below minimum")
    assert gt.check_course_grade_range("Medicina", 150, DF)["points_needed_for_minimum"] == 10
    assert gt.check_course_grade_range("Medicina", 185, DF)["status"].startswith("Excellent")
    assert gt.check_course_grade_range("Medicina", 163, DF)["status"].startswith("Borderline")
    assert gt.check_course_grade_range("Medicina", 177, DF)["status"].startswith("Strong")
    assert gt.check_course_grade_range("direito", 170, DF)["found"] == 0
    assert "valid entry grades" in gt.check_course_grade_range("Dentária", 170, DF)["message"]


class FakeModel:
    def __init__(self, answer): self.answer, self.calls = answer, []
    def generate_content_multimodal(self, **kw): self.calls.append(kw); return self.answer
    def generate_content(self, **kw): self.calls.append(kw); return self.answer


def test_extraction_portuguese_and_fence():
    answer = '```json\n{"student_type":"portuguese","current_year":"11th Grade","track":"Artes Visuais","grades":{"10th":{"Português":15}}}\n```'
    m = FakeModel(answer)
    out = gt.extract_grades_from_file(b"img", "image/png", "portuguese", model=m)
    assert out == {"student_type": "portuguese", "current_year": "11th Grade", "track": "Artes Visuais",
                   "grades": {"10th": {"Português": 15}}, "input_method": "upload"}
    assert m.calls[0]["temperature"] == 0.1 and m.calls[0]["mime_type"] == "image/png"
    assert "PORTUGUESE" in m.calls[0]["prompt"]


def test_extraction_international_and_errors():
    m = FakeModel('{"student_type":"international","subjects":[{"name":"Maths","grade":"A","year":"12th"}]}')
    out = gt.extract_grades_from_file(b"x", "application/pdf", "international", model=m)
    assert out["country"] == "Unknown" and out["subjects"][0]["name"] == "Maths" and "INTERNATIONAL" in m.calls[0]["prompt"]
    with pytest.raises(gt.GradeExtractionError):
        gt.extract_grades_from_file(b"x", "image/png", "portuguese", model=FakeModel("not json"))


def test_overview_prompt_and_call():
    m = FakeModel("overview")
    data = {"country": "UK", "grade_scale": "A-F", "subjects": [{"name": "Maths", "grade": "A", "year": "12th"}]}
    assert gt.generate_international_overview(data, model=m) == "overview"
    assert "- Maths: A (12th)" in m.calls[0]["prompt"] and m.calls[0]["temperature"] == 0.7
