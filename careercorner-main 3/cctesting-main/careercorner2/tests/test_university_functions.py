import sys
import types

import pandas as pd
import pytest

from services import chat_functions as cf
from services import university_functions as uf

DF = pd.DataFrame({
    "course_code": ["9119", "9120", "L344", "8086"],
    "institution_name": ["IST", "NOVA FCT", "Açores", "Açores"],
    "course_name": ["Engenharia Informática e de Computadores", "Engenharia Informática", "Guias de Natureza", "Medicina Veterinária"],
    "degree_type": ["L1", "L1", "L1", "MI"],
    "placed": [100.0, 90.0, 6.0, 22.0],
    "last_grade": [172.0, 138.5, 119.5, None],
    "region": ["Lisboa", "Lisboa", "Other", "Other"],
    "type": ["Public"] * 4,
    "lat": [38.7, 38.66, None, None],
    "lon": [-9.1, -9.2, None, None],
})


@pytest.fixture
def env(monkeypatch):
    saved = []
    profiles = {}
    mod = types.ModuleType("utils.database")
    mod.load_student_profile = lambda uid: dict(profiles.get(uid, {}))
    mod.save_student_profile = lambda uid, d: profiles.__setitem__(uid, dict(d)) or True

    def save_university(uid, data):
        if any(s[0] == uid and s[1]["name"] == data["name"] and s[1]["program_name"] == data["program_name"] for s in saved):
            return False
        saved.append((uid, data))
        return True

    mod.save_university = save_university
    mod.get_saved_universities = lambda uid: [dict(d, saved_at="2026-10-13") for u, d in saved if u == uid]
    mod.remove_saved_university = lambda uid, inst, prog: bool([saved.remove(s) for s in list(saved)
                                                               if s[0] == uid and s[1]["name"] == inst and s[1]["program_name"] == prog])
    monkeypatch.setitem(sys.modules, "utils.database", mod)
    import utils
    monkeypatch.setattr(utils, "database", mod, raising=False)
    monkeypatch.setattr(uf, "load_dges_df", lambda: DF.copy())
    cf.load_all()
    return types.SimpleNamespace(saved=saved, profiles=profiles)


def test_search_without_grade_has_no_colours(env):
    out = cf.call_function("search_universities", {"degree_name": "informatica"}, "guest-ab12cd34")["result"]
    assert out["total_found"] == 2 and out["display"] == "map"
    first = out["universities"][0]
    assert first["institution_name"] == "IST" and first["last_grade_200"] == 172.0 and first["last_grade_20"] == 17.2
    assert first["chance"] == "unknown" and first["map_color"] == "grey" and first["coordinates"] == {"lat": 38.7, "lon": -9.1}


def test_search_with_grade_colours_like_the_proposal(env):
    out = cf.call_function("search_universities", {"degree_name": "Engenharia Informática", "grade_200": 178}, "guest-ab12cd34")["result"]
    by = {u["institution_name"]: u for u in out["universities"]}
    assert by["IST"]["chance"] == "target" and by["IST"]["map_color"] == "yellow" and by["IST"]["margin_200"] == 6.0
    assert by["NOVA FCT"]["chance"] == "safe" and by["NOVA FCT"]["map_color"] == "green"
    low = cf.call_function("search_universities", {"degree_name": "Engenharia Informática", "grade_200": 140}, "guest-ab12cd34")["result"]
    assert {u["institution_name"]: u["map_color"] for u in low["universities"]}["IST"] == "red"


def test_saved_grade_is_used_automatically(env):
    env.profiles["ana@x.com"] = {"grades_data": {"grades": {"10th": {"P": 17.8}, "11th": {}, "12th": {}, "exams": {}},
                                                 "current_year": "10th Grade"}}
    out = cf.call_function("search_universities", {"degree_name": "informatica"}, "ana@x.com")["result"]
    assert out["grade_used_200"] == pytest.approx(178.0) and out["universities"][0]["map_color"] == "yellow"


def test_missing_values_and_filters(env):
    out = uf.search_programs("medicina", df=DF)
    vet = out["universities"][0]
    assert vet["last_grade_200"] is None and vet["coordinates"] is None and vet["degree_level"] == "Integrated Master's"
    assert out["without_map_pin"] == 1
    assert uf.search_programs("informatica", region="lisboa", df=DF)["total_found"] == 2
    assert uf.search_programs("informatica", region="porto", df=DF)["total_found"] == 0
    assert uf.search_programs("informatica", limit=1, df=DF)["shown"] == 1
    none = cf.call_function("search_universities", {"degree_name": "direito"}, "ana@x.com")["result"]
    assert none["total_found"] == 0 and "No programs found" in none["message"]


def test_save_list_duplicate_remove(env):
    args = {"course_code": "9119", "institution_name": "IST"}
    assert not cf.call_function("save_university", args, "guest-ab12cd34")["ok"]
    out = cf.call_function("save_university", args, "ana@x.com")["result"]
    assert out["saved"] and out["institution_name"] == "IST"
    record = env.saved[0][1]
    assert record["name"] == "IST" and record["average_grade_required"] == "17.20/20" and record["last_grade_200"] == 172.0
    assert record["course_code"] == "9119" and record["coordinates"]
    again = cf.call_function("save_university", args, "ana@x.com")["result"]
    assert not again["saved"] and again["already_saved"]
    listed = cf.call_function("get_saved_universities", {}, "ana@x.com")["result"]
    assert listed["count"] == 1 and "chance" not in listed["universities"][0]
    env.profiles["ana@x.com"] = {"grades_data": {"grades": {"10th": {"P": 17.8}, "11th": {}, "12th": {}, "exams": {}}, "current_year": "10th Grade"}}
    assert cf.call_function("get_saved_universities", {}, "ana@x.com")["result"]["universities"][0]["chance"] == "target"
    assert cf.call_function("remove_saved_university", {"institution_name": "IST", "program_name": "Engenharia Informática e de Computadores"}, "ana@x.com")["result"]["removed"]
    assert cf.call_function("get_saved_universities", {}, "ana@x.com")["result"]["count"] == 0


def test_unknown_program_is_not_saved(env):
    out = cf.call_function("save_university", {"course_code": "0000", "institution_name": "IST"}, "ana@x.com")["result"]
    assert not out["saved"] and "not found" in out["error"] and env.saved == []


def test_saved_universities_feed_the_comparison(env):
    cf.call_function("save_university", {"course_code": "9120", "institution_name": "NOVA FCT"}, "ana@x.com")
    out = cf.call_function("compare_saved_universities", {"grade_200": 178}, "ana@x.com")["result"]
    assert out[0]["name"] == "NOVA FCT" and out[0]["status"] == "safe"
