import json
import sys
import types

import pandas as pd
import pytest

from services import chat_functions as cf
from services import quiz_functions as qf

DF = pd.DataFrame({"course_name": [
    "Engenharia Informática", "Engenharia Informática (Ensino em Inglês)", "Engenharia Informática e de Computadores",
    "Engenharia de Sistemas Informáticos", "Ciência de Dados", "Design de Comunicação", "Medicina", "Direito",
    "Gestão de Sistemas de Informação",
]})
TECH = ["Engenharia Informática", "Engenharia Informática e de Computadores", "Engenharia de Sistemas Informáticos",
        "Ciência de Dados", "Gestão de Sistemas de Informação"]

REPORT = """# Your Career Discovery Results

## Top Career Sectors & Paths

### 1. Technology (70%)

**Why this sector:** curious.

### 2. Creative Arts (30%)

**Why this sector:** playful.

## Your Hidden Strengths
1. **Curiosity**: opened the door
"""


class FakeModel:
    """Answers each kind of request the quizzes make."""

    def __init__(self):
        self.calls = []
        self.fail = set()
        self.eliminate = {}

    def generate_content(self, prompt, system_instruction=None, temperature=None, user_id=None, session_id=None, metadata=None):
        kind = metadata["type"]
        self.calls.append(kind)
        if kind in self.fail:
            raise RuntimeError("model down")
        if kind == "adaptive_career_question":
            return f"Sector question {prompt.count('Q')}?"
        if kind == "career_discovery_report":
            return REPORT
        if kind == "degree_quiz_candidates":
            return "Here you go: " + json.dumps(TECH + ["Not a real degree"])
        if kind == "degree_quiz_question":
            return json.dumps({"question": f"Degree question {len(self.calls)}?"})
        if kind == "degree_quiz_eliminate":
            answer = prompt.split("Student's answer:")[1].split("\n")[0].strip()
            return json.dumps({"eliminate": self.eliminate.get(answer, [])})
        if kind == "degree_quiz_final":
            names = [l for l in prompt.split("Degrees left:\n")[1].split("\n\n")[0].split("\n")]
            return "```json\n" + json.dumps({"top": [{"degree": n, "reason": f"Fits {n}"} for n in names[:3]]}) + "\n```"
        raise AssertionError(kind)


@pytest.fixture
def env(monkeypatch):
    model = FakeModel()
    monkeypatch.setattr(qf, "_model", model)
    monkeypatch.setattr(qf, "load_dges_df", lambda: DF.copy())
    reports = []
    mod = types.ModuleType("utils.database")
    mod.save_report = lambda **kw: reports.append(kw) or len(reports)
    monkeypatch.setitem(sys.modules, "utils.database", mod)
    import utils
    monkeypatch.setattr(utils, "database", mod, raising=False)
    cf.load_all()
    return types.SimpleNamespace(model=model, reports=reports, session={})


def call(env, name, args=None, user="guest-ab12cd34"):
    out = cf.call_function(name, args or {}, user, env.session)
    assert out["ok"], out
    return out["result"]


def test_degree_names_fold_variants():
    assert qf.degree_names(DF)[:3] == ["Ciência de Dados", "Design de Comunicação", "Direito"]
    assert qf.degree_names(DF).count("Engenharia Informática") == 1


def test_sector_quiz_full_run(env):
    out = call(env, "sector_quiz")
    assert not out["done"] and out["question_number"] == 1 and out["total_questions"] == 10 and out["question"]
    assert call(env, "sector_quiz")["question_number"] == 1  # asking again doesn't advance
    for i in range(9):
        out = call(env, "sector_quiz", {"answer": f"answer {i}"})
        assert not out["done"] and out["question_number"] == i + 2
    out = call(env, "sector_quiz", {"answer": "last"})
    assert out["done"] and out["sectors"] == {"Technology": 70, "Creative Arts": 30}
    assert out["primary_sector"] == "Technology" and out["questions_answered"] == 10
    assert env.model.calls.count("adaptive_career_question") == 10


def test_sector_quiz_finish_early_and_restart(env):
    call(env, "sector_quiz")
    call(env, "sector_quiz", {"answer": "a"})
    early = call(env, "sector_quiz", {"answer": "b", "finish_now": True})
    assert not early["done"]  # needs 3 answers
    done = call(env, "sector_quiz", {"answer": "c", "finish_now": True})
    assert done["done"] and done["questions_answered"] == 3
    again = call(env, "sector_quiz")
    assert not again["done"] and again["question_number"] == 1


def test_sector_question_falls_back_when_model_fails(env):
    env.model.fail.add("adaptive_career_question")
    out = call(env, "sector_quiz")
    assert out["question"] == qf.FALLBACK_QUESTIONS[0]


def test_sector_save_needs_login_and_a_result(env):
    assert not cf.call_function("save_sector_result", {}, "guest-ab12cd34", env.session)["ok"]
    assert not call(env, "save_sector_result", user="ana@x.com")["saved"]
    call(env, "sector_quiz")
    for i in range(10):
        call(env, "sector_quiz", {"answer": f"a{i}"})
    assert call(env, "save_sector_result", user="ana@x.com")["saved"]
    kw = env.reports[0]
    assert kw["report_type"] == "career_quiz" and kw["title"].startswith("Career Quiz - Technology - ")
    assert kw["cv_data"]["recommended_sectors"] == {"Technology": 70, "Creative Arts": 30}
    assert kw["cv_data"]["sectors_display"] == "Technology (70%), Creative Arts (30%)"


def test_degree_quiz_needs_a_field(env):
    out = call(env, "degree_quiz")
    assert not out["done"] and "which field" in out["error"]


def test_degree_quiz_eliminates_down_to_three(env):
    env.model.eliminate = {"back end": ["Ciência de Dados"], "coding": ["Gestão de Sistemas de Informação"]}
    out = call(env, "degree_quiz", {"field": "computer science"})
    assert not out["done"] and out["question_number"] == 1 and out["degrees_still_possible"] == 5
    out = call(env, "degree_quiz", {"answer": "back end"})
    assert out["degrees_still_possible"] == 4 and out["just_ruled_out"] == ["Ciência de Dados"] and out["question_number"] == 2
    out = call(env, "degree_quiz", {"answer": "coding"})
    assert out["done"] and out["questions_asked"] == 2
    assert [p["degree"] for p in out["top_degrees"]] == [
        "Engenharia Informática", "Engenharia Informática e de Computadores", "Engenharia de Sistemas Informáticos"]
    assert out["top_degrees"][0]["reason"] == "Fits Engenharia Informática"
    assert "Not a real degree" not in str(out)


def test_degree_quiz_never_goes_below_three_and_stops_at_fifteen(env):
    env.model.eliminate = {"drop all": TECH}
    call(env, "degree_quiz", {"field": "tech"})
    out = call(env, "degree_quiz", {"answer": "drop all"})
    assert out["done"] and len(out["top_degrees"]) == 3  # eliminations were capped at 5 - 3 = 2

    env2 = types.SimpleNamespace(model=env.model, session={})
    env.model.eliminate = {}
    call(env2, "degree_quiz", {"field": "tech"})
    for i in range(14):
        out = call(env2, "degree_quiz", {"answer": f"meh {i}"})
        assert not out["done"]
    out = call(env2, "degree_quiz", {"answer": "last"})
    assert out["done"] and out["questions_asked"] == 15 and len(out["top_degrees"]) == 3


def test_degree_quiz_survives_a_bad_elimination_answer(env):
    original = env.model.generate_content

    def flaky(**kw):
        if kw["metadata"]["type"] == "degree_quiz_eliminate":
            return "not json at all"
        return original(**kw)

    env.model.generate_content = lambda prompt, **kw: flaky(prompt=prompt, **kw)
    call(env, "degree_quiz", {"field": "tech"})
    out = call(env, "degree_quiz", {"answer": "anything"})
    assert not out["done"] and out["degrees_still_possible"] == 5


def test_degree_quiz_too_few_matches_and_new_field_restarts(env):
    real = env.model.generate_content

    def few(prompt, **kw):
        if kw["metadata"]["type"] == "degree_quiz_candidates":
            return json.dumps(["Medicina"])
        return real(prompt, **kw)

    env.model.generate_content = few
    out = call(env, "degree_quiz", {"field": "medicine"})
    assert "Only 1 degree" in out["error"]
    env.model.generate_content = real
    first = call(env, "degree_quiz", {"field": "tech"})
    again = call(env, "degree_quiz", {"field": "tech"})
    assert again["question_number"] == first["question_number"] == 1  # same field: no restart
    assert call(env, "degree_quiz", {"field": "computing"})["question_number"] == 1  # new field restarts


def test_degree_save_matches_the_old_degree_report_format(env):
    call(env, "degree_quiz", {"field": "tech"})
    env.model.eliminate = {"x": ["Ciência de Dados", "Gestão de Sistemas de Informação"]}
    call(env, "degree_quiz", {"answer": "x"})
    assert call(env, "save_degree_results", user="ana@x.com")["saved"]
    kw = env.reports[0]
    assert kw["report_type"] == "degree" and kw["title"].startswith("Degree Quiz - tech - ")
    assert kw["cv_data"]["degrees"] == ["Engenharia Informática", "Engenharia Informática e de Computadores", "Engenharia de Sistemas Informáticos"]
    from utils.saved_data import extract_degree_names
    assert extract_degree_names(kw["content"]) == kw["cv_data"]["degrees"]
    assert not cf.call_function("save_degree_results", {}, "guest-ab12cd34", env.session)["ok"]
