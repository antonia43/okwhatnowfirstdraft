import sys
import types

import pytest

from services import chat_functions as cf
from services import profile_functions as pf
from services import resource_functions as rf
from utils.gemini_key import get_gemini_api_key


class FakeTools:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def _answer(self, name, *args):
        self.calls.append((name, args))
        if not self.ok:
            return {"success": False, "error": "no key"}
        return {"success": True, "answer": f"{name} {args}", "sources": [{"title": "T", "url": "https://x"}]}

    def get_study_resources_web(self, *a): return self._answer("study", *a)
    def get_career_options(self, *a): return self._answer("career", *a)
    def get_wage_info(self, *a): return self._answer("wage", *a)
    def get_city_guide(self, *a): return self._answer("city", *a)


@pytest.fixture
def tools(monkeypatch):
    fake = FakeTools()
    monkeypatch.setattr(rf, "_tools", fake)
    cf.load_all()
    return fake


def call(name, args=None, user="guest-ab12cd34", session=None):
    return cf.call_function(name, args or {}, user, session)


def test_links_work_for_guests(tools):
    assert len(call("get_exam_papers")["result"]["links"]) == 2
    assert [s["name"] for s in call("get_scholarships")["result"]["scholarships"]] == [
        "DGES Scholarships", "FCT Research Grants", "Erasmus+ Mobility"]


def test_searches_pass_the_old_arguments(tools):
    assert call("find_study_resources", {"subject": " Python "})["result"]["answer"].startswith("study ('Python',)")
    assert tools.calls[-1] == ("study", ("Python",))
    call("explore_career_options", {"degree": "Psychology"})
    call("find_salaries", {"job_title": "Nurse"})
    assert tools.calls[-1] == ("wage", ("Nurse", "Portugal"))
    call("find_salaries", {"job_title": "Nurse", "country": "Spain"})
    assert tools.calls[-1] == ("wage", ("Nurse", "Spain"))
    call("get_city_guide", {"city": "Porto", "country": "Portugal"})
    assert tools.calls[-1] == ("city", ("Porto", "Portugal"))
    assert call("find_study_resources", {"subject": "x"})["result"]["sources"][0]["url"] == "https://x"


def test_empty_input_and_search_failure_are_explained(tools):
    out = call("find_study_resources", {"subject": "  "})
    assert not out["ok"] and "which subject" in out["error"]
    tools.ok = False
    out = call("get_city_guide", {"city": "Porto"})
    assert not out["ok"] and "no key" in out["error"]


@pytest.fixture
def db(monkeypatch):
    mod = types.ModuleType("utils.database")
    mod.profile = {"grades_data": None}
    mod.reports = {}
    mod.unis = []
    mod.load_student_profile = lambda uid: dict(mod.profile)
    mod.save_student_profile = lambda uid, data: mod.profile.update(data) or True
    mod.load_reports = lambda uid, t: mod.reports.get(t, [])
    mod.get_saved_universities = lambda uid: mod.unis
    monkeypatch.setitem(sys.modules, "utils.database", mod)
    import utils
    monkeypatch.setattr(utils, "database", mod, raising=False)
    cf.load_all()
    return mod


def test_guest_profile_is_empty_and_cannot_save(db):
    assert call("get_student_profile")["result"]["signed_in"] is False
    assert not call("update_student_profile", {"interests": "art"})["ok"]


def test_profile_remembers_and_clears_details(db):
    out = call("update_student_profile", {"interests": " art ", "school_year": "12th"}, user="ana@x.com")
    assert out["result"]["about"] == {"interests": "art", "school_year": "12th"}
    call("update_student_profile", {"interests": "", "notes": "wants Lisbon"}, user="ana@x.com")
    assert call("get_student_profile", user="ana@x.com")["result"]["about"] == {"school_year": "12th", "notes": "wants Lisbon"}
    assert not call("update_student_profile", {}, user="ana@x.com")["ok"]
    assert not call("update_student_profile", {"favourite_colour": "red"}, user="ana@x.com")["ok"]


def test_profile_summarises_saved_things_and_keeps_grades(db):
    db.reports = {
        "career_quiz": [{"cv_data": {"recommended_sector": "Technology", "recommended_sectors": {"Technology": 100}}}],
        "degree": [{"cv_data": '{"degrees": ["Medicina"], "field": "health"}'}],
    }
    db.unis = [{}, {}]
    db.profile = {"grades_data": {"school": {"x": 1}}}
    out = call("update_student_profile", {"track": "Sciences"}, user="ana@x.com")
    assert db.profile["grades_data"] == {"school": {"x": 1}}  # untouched by profile updates
    profile = call("get_student_profile", user="ana@x.com")["result"]
    assert profile["sector_quiz"]["top_sector"] == "Technology"
    assert profile["degree_quiz"] == {"field": "health", "top_degrees": ["Medicina"]}
    assert profile["saved_universities_count"] == 2 and profile["about"] == {"track": "Sciences"}


def test_gemini_key_accepts_either_name(monkeypatch):
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", None)
    assert get_gemini_api_key() is None
    monkeypatch.setenv("GEMINI_API_KEY", "g1")
    assert get_gemini_api_key() == "g1"
    monkeypatch.setenv("GOOGLE_API_KEY", "g2")
    assert get_gemini_api_key() == "g2"
