"""Entry requirements, what-if scenarios, safer alternatives and the source line (uses the real DGES data files)."""
from services import chat_helpers as h
from services import chat_functions as cf
from utils.dges_requirements import _student_exams, admission_for, exam_average_needed, requirements_for, what_if

IST = ("9121", "Universidade de Lisboa - Instituto Superior Técnico")
GRADES = [{"name": n, "grade": g, "period": p} for n, g, p in [
    ("Matemática A", 16, "10th"), ("Matemática A", 15, "11th"), ("Matemática A", 16, "12th"),
    ("Física e Química A", 14, "10th"), ("Física e Química A", 14, "11th"), ("Física e Química A", 15, "12th"),
    ("Português", 15, "10th"), ("Português", 14, "11th"), ("Português", 15, "12th"),
    ("Matemática A (635)", 150, "exam"), ("Física e Química A (715)", 140, "exam")]]


def setup_module(module):
    cf.load_all()


def test_matematica_a_counts_for_programs_that_list_plain_matematica():
    assert _student_exams({"Matemática A (635)": 150})["matematica"] == 150
    req = {"exam_rule": "all", "exam_sets": [["Matemática"]], "w_secondary": 50, "w_exams": 50,
           "min_exams": None, "min_application": None}
    assert admission_for(req, 150, {"Matemática A (635)": 150})["status"] == "ok"


def test_what_if_and_exam_average_needed():
    req = requirements_for(*IST)
    base = admission_for(req, 150, {"Matemática A": 140, "Física e Química A": 140})["admission_grade_200"]
    more = what_if(req, 150, {"Matemática A": 140, "Física e Química A": 140}, exam_boost=10)["admission_grade_200"]
    assert round(more - base, 1) == 5.0  # exams weigh 50%
    assert exam_average_needed(req, 150, 165.3) == 180.6
    assert exam_average_needed(req, 100, 190) is None  # more than 200 needed


def test_check_program_gives_points_short_and_scenarios():
    out = cf.call_function("check_program_requirements",
                           {"course_code": IST[0], "institution_name": IST[1], "entries": GRADES}, "guest-1")["result"]
    assert out["chance"] == "reach" and out["points_short_of_last_cutoff"] > 0
    assert len(out["what_if_scenarios"]) == 3
    custom = cf.call_function("check_program_requirements",
                              {"course_code": IST[0], "institution_name": IST[1], "entries": GRADES,
                               "exam_boost_200": 30}, "guest-1")["result"]
    assert custom["what_if"]["admission_grade_200"] > out["admission_grade_200"]


def test_safer_alternatives_are_safe_or_target_and_similar():
    out = cf.call_function("find_safer_alternatives",
                           {"course_code": IST[0], "institution_name": IST[1], "entries": GRADES}, "guest-1")["result"]
    assert out["display"] == "map" and out["universities"]
    assert all(p["chance"] in ("safe", "target") for p in out["universities"])
    assert all(p["why_similar"] for p in out["universities"])
    assert not any(p["course_code"] == IST[0] and p["institution_name"] == IST[1] for p in out["universities"])


def test_safer_alternatives_need_grades():
    out = cf.call_function("find_safer_alternatives", {"course_code": IST[0], "institution_name": IST[1]}, "guest-1")
    assert "No grades" in out["result"]["error"]


def test_sources_line_names_only_what_ran():
    events = [{"name": "check_program_requirements", "ok": True, "result": {}},
              {"name": "search_degree_info", "ok": True,
               "result": {"passages": [{"school": "NOVA FCT", "source_url": "https://www.fct.unl.pt/x"}]}},
              {"name": "find_study_resources", "ok": False, "error": "x"}]
    line = h.sources_line(h.sources_for(events))
    assert "DGES course page" in line and "NOVA FCT degree page](https://www.fct.unl.pt/x)" in line
    assert "study resources" not in line
    assert h.sources_line(h.sources_for([{"name": "sector_quiz", "ok": True, "result": {}}])) == ""


def test_follow_up_buttons_only_when_not_safe():
    base = {"name": "check_program_requirements", "args": {"course_code": "1", "institution_name": "X"}, "ok": True}
    reach = {**base, "result": {"chance": "reach", "admission_grade_200": 140, "program_name": "P", "institution_name": "X"}}
    safe = {**base, "result": {"chance": "safe", "admission_grade_200": 190, "program_name": "P", "institution_name": "X"}}
    assert len(h.follow_up_buttons([reach])) == 2 and h.follow_up_buttons([safe]) == []
