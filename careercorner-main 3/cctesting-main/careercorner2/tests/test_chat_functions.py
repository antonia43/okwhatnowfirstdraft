import sys
import types

import pytest

from services import chat_functions as cf


@pytest.fixture
def db(monkeypatch):
    """In-memory stand-in for utils.database."""
    store = {}
    mod = types.ModuleType("utils.database")
    mod.load_student_profile = lambda uid: dict(store.get(uid, {}))
    mod.save_student_profile = lambda uid, data: store.__setitem__(uid, dict(data)) or True
    mod.get_saved_universities = lambda uid: []
    monkeypatch.setitem(sys.modules, "utils.database", mod)
    import utils
    monkeypatch.setattr(utils, "database", mod, raising=False)
    cf.load_all()
    return store


ENTRIES = [
    {"name": "Português", "grade": 16, "period": "10th"},
    {"name": "Matemática A", "grade": 18, "period": "11th"},
    {"name": "Matemática A (635)", "grade": 170, "period": "exam"},
]


def test_declarations_have_the_gemini_shape(db):
    decls = {d["name"]: d for d in cf.get_declarations()}
    assert {"calculate_admission_grade", "save_grades", "get_saved_grades",
            "check_chances_for_degree", "compare_saved_universities"} <= set(decls)
    for d in decls.values():
        assert d["description"] and d["parameters"]["type"] == "object"
    assert "user_id" not in str(decls)
    assert decls["save_grades"]["parameters"]["required"] == ["entries"]


def test_unknown_function_and_missing_args(db):
    assert not cf.call_function("nope", {}, "ana@x.com")["ok"]
    out = cf.call_function("save_grades", {}, "ana@x.com")
    assert not out["ok"] and "entries" in out["error"]


def test_guest_cannot_save_but_can_calculate(db):
    out = cf.call_function("save_grades", {"entries": ENTRIES}, "guest-ab12cd34")
    assert not out["ok"] and "log in" in out["error"] and db == {}
    out = cf.call_function("calculate_admission_grade", {"entries": ENTRIES}, "guest-ab12cd34")
    assert out["ok"] and out["result"]["cif_200"] > 0


def test_model_cannot_choose_the_user(db):
    cf.call_function("save_grades", {"entries": ENTRIES, "user_id": "victim@x.com"}, "ana@x.com")
    assert "ana@x.com" in db and "victim@x.com" not in db


def test_save_then_read_back_and_correct(db):
    out = cf.call_function("save_grades", {"entries": ENTRIES, "current_year": "12th Grade (Completed)"}, "ana@x.com")
    assert out["ok"] and out["result"]["saved"] and out["result"]["cif_200"] > 0
    got = cf.call_function("get_saved_grades", {}, "ana@x.com")["result"]
    assert got["has_grades"] and got["grades_data"]["grades"]["exams"]["Matemática A (635)"] == 170
    cf.call_function("save_grades", {"entries": [{"name": "Matemática A (635)", "grade": 180, "period": "exam"}]}, "ana@x.com")
    again = cf.call_function("get_saved_grades", {}, "ana@x.com")["result"]
    assert again["grades_data"]["grades"]["exams"]["Matemática A (635)"] == 180
    assert again["grades_data"]["grades"]["10th"]["Português"] == 16  # earlier grades kept


def test_nothing_saved_yet(db):
    assert cf.call_function("get_saved_grades", {}, "new@x.com")["result"] == {"has_grades": False}
    out = cf.call_function("calculate_admission_grade", {}, "new@x.com")
    assert out["ok"] and "No grades yet" in out["result"]["error"]


def test_scale_mistakes_are_reported(db):
    bad = [{"name": "Matemática A (635)", "grade": 18, "period": "10th"}, {"name": "X", "grade": 25, "period": "11th"}]
    out = cf.call_function("calculate_admission_grade", {"entries": bad}, "ana@x.com")
    assert not out["ok"] and "outside the 0-20" in out["error"]


def test_weights_change_the_result(db):
    entries = [{"name": "Português", "grade": 16, "period": "10th"}, {"name": "Português (639)", "grade": 130, "period": "exam"}]
    a = cf.call_function("calculate_admission_grade", {"entries": entries, "current_year": "12th Grade (Completed)", "weights": "exam_heavy"}, "ana@x.com")
    b = cf.call_function("calculate_admission_grade", {"entries": entries, "current_year": "12th Grade (Completed)", "weights": "secondary_heavy"}, "ana@x.com")
    assert a["result"]["cif_200"] != b["result"]["cif_200"]


def test_chances_without_a_grade_gives_the_range(db, monkeypatch):
    import pandas as pd
    df = pd.DataFrame({"institution_name": ["A", "B"], "course_name": ["Medicina", "Medicina"], "last_grade": [180.0, 160.0]})
    monkeypatch.setattr("services.grade_tools.find_programs", lambda name, d=None: df)
    out = cf.call_function("check_chances_for_degree", {"degree_name": "Medicina"}, "ana@x.com")["result"]
    assert out["lowest_entry"] == 160 and out["highest_entry"] == 180 and "status" not in out
    out = cf.call_function("check_chances_for_degree", {"degree_name": "Medicina", "grade_200": 170}, "ana@x.com")["result"]
    assert out["status"].startswith("Moderate")


def test_duplicate_names_are_refused():
    with pytest.raises(ValueError):
        cf.chat_function("get_saved_grades", "again")(lambda user_id: None)
