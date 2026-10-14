"""The two quizzes the chat can run. Both are optional and independent.

- sector_quiz: 10 playful, indirect questions that point to broad career sectors
  (for students who don't know their sector yet). Prompts are the Career Corner originals.
- degree_quiz: for a student who names a field. Starts from the real DGES degree names,
  and each answer rules some of them out until 3 are left (3 to 15 questions).

The chat asks each question and passes the student's answer back. Progress is kept in the
chat's session scratch space, so guests can take the quizzes too. Saving needs a login.
"""
import json
import re
from datetime import datetime

from services.chat_functions import chat_function
from utils.dges import load_dges_df

# ---- shared helpers -----------------------------------------------------------

_model = None  # tests put a fake here


def _get_model():
    if _model is not None:
        return _model
    from services.grade_tools import _default_model

    return _default_model()


def _ask(prompt, system_instruction, temperature, kind, user_id=None):
    return _get_model().generate_content(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        user_id=user_id,
        session_id=None,
        metadata={"type": kind},
    )


def _parse_json(text):
    """JSON from a model answer, even when wrapped in a code fence or extra words."""
    text = (text or "").strip()
    text = re.sub(r"^\x60\x60\x60(?:json)?|\x60\x60\x60$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if not match:
            raise ValueError("The AI answer was not valid JSON")
        return json.loads(match.group(1))


# ---- sector quiz --------------------------------------------------------------

SECTOR_QUESTIONS = 10
SECTOR_MIN_TO_FINISH = 3
SECTORS = ("Technology, Healthcare, Business, Engineering, Creative Arts, Education, Science, Law, "
           "Social Services, Media & Communications, Hospitality, Sports & Fitness, Environment, Public Service")
FALLBACK_QUESTIONS = [
    "You find a mysterious door in your house. Do you open it?",
    "Would you rather explore space or the deep ocean?",
    "What's the best gift you've ever received?",
    "You have a free Saturday. What are you most excited to do?",
    "Mountains or beach for a week-long vacation?",
    "You won a million dollars. First thing you buy?",
    "What superpower would make your daily life easier?",
    "Dinner party with 3 famous people. Who do you invite?",
    "Your phone dies for a whole day. How do you feel?",
    "What childhood hobby do you wish you kept doing?",
]
_SECTOR_HEADING = re.compile(r"###\s*\d+\.\s*([A-Za-z\s&]+)\s*\((\d+)%\)")


def _next_sector_question(answers, user_id):
    q_num = len(answers)
    context = ""
    if answers:
        context = "Previous answers:\n" + "\n".join(
            f"Q{a['number']}: {a['question']}\nA: {a['answer'][:100]}..." for a in answers[-3:])
    prompt = f"""You are a creative career counselor designing a fun, engaging personality quiz.

Current question number: {q_num + 1} of {SECTOR_QUESTIONS}

{context if context else "This is the first question."}

CRITICAL RULES - NO EXCEPTIONS:
1. ONE question ONLY
2. 15 WORDS MAXIMUM
3. NO career/job/school/work references EVER
4. NO abstract philosophical questions (avoid "meaning of life" type questions)
5. Make it FUN, relatable, and concrete
6. Questions should be about PREFERENCES, SCENARIOS, or REACTIONS
7. NO questions from ANY previous conversation

GOOD QUESTION TYPES:
- Scenarios: "You find $100 on the street. What do you do?"
- Preferences: "Would you rather live in the mountains or by the ocean?"
- Reactions: "A friend cancels plans last minute. How do you feel?"
- Imagination: "You can have dinner with anyone, dead or alive. Who?"
- Memories: "What's your favorite childhood memory?"
- Choices: "Netflix all day or outdoor adventure?"

BAD QUESTION TYPES:
- Too abstract: "What gives your life purpose?"
- Too philosophical: "What is the nature of consciousness?"
- Too vague: "How do you see yourself?"
- Career-related: "What job interests you?"

REVEAL: personality traits, values, thinking style, preferences

Return ONLY the question. NO explanation."""
    try:
        question = _ask(
            prompt,
            "Return ONLY one fun, concrete question under 15 words. NO abstract philosophy. "
            "NO career references. Make it relatable and easy to answer.",
            0.8, "adaptive_career_question", user_id).strip()
        if question:
            return question
    except Exception:
        pass
    return FALLBACK_QUESTIONS[q_num % len(FALLBACK_QUESTIONS)]


def _sector_report(answers, user_id):
    qa_text = "\n\n".join(f"Q{a['number']}: {a['question']}\nAnswer: {a['answer']}" for a in answers)
    prompt = f"""You are an expert career psychologist analyzing quiz responses to find the BEST career sectors for this student.

QUIZ RESPONSES:
{qa_text}

ANALYSIS TASK:
1. Identify TOP 1-3 BROAD SECTORS with fit percentages (must add to 100%)
2. Within each sector, find 2-3 SPECIFIC CAREER PATHS
3. Reveal hidden skills with evidence from answers

BROAD SECTORS TO CHOOSE FROM:
{SECTORS}

IMPORTANT RULES:
- Give 1-3 broad sectors with percentages that SUM TO 100%
- If only 1 sector fits → give it 100%
- If 2-3 sectors → split the percentage (e.g., Healthcare 60%, Education 40%)
- Then for EACH sector, list specific career paths

OUTPUT FORMAT (strict markdown):

# Your Career Discovery Results

## Top Career Sectors & Paths

### 1. Healthcare (60%)

**Why this sector:**
[2-3 sentences with evidence from their answers]

**Specific career paths within Healthcare:**
- **Nursing**: [Why it fits]
- **Physiotherapy**: [Why it fits]
- **Pharmacy**: [Why it fits]

**Degrees to explore:**
- Nursing
- Physiotherapy
- Pharmacy

---

### 2. Education (40%)

**Why this sector:**
[2-3 sentences with evidence from their answers]

**Specific career paths within Education:**
- **Primary Teacher**: [Why it fits]
- **Educational Psychologist**: [Why it fits]
- **Special Needs Coordinator**: [Why it fits]

**Degrees to explore:**
- Primary Education
- Educational Psychology
- Special Education

---

## Your Hidden Strengths

1. **[Skill Name]**: [Evidence from answer]
2. **[Skill Name]**: [Evidence from answer]
3. **[Skill Name]**: [Evidence from answer]
4. **[Skill Name]**: [Evidence from answer]

## Next Steps

1. Explore degrees in [Primary Sector]
2. Research careers: [3 specific job titles]
3. Develop: [2 skills to enhance fit]

## Your Profile Summary
[2-3 sentences describing unique approach/style/values]

---
*Report generated {datetime.now().strftime('%Y-%m-%d')}*
"""
    return _ask(prompt, "You are an expert career psychologist. Give broad sectors with % AND specific paths within them.",
                0.6, "career_discovery_report", user_id)


def parse_sectors(report):
    """{'Healthcare': 60, 'Education': 40} from the report headings, and the biggest one."""
    sectors = {name.strip(): int(pct) for name, pct in _SECTOR_HEADING.findall(report or "")}
    primary = max(sectors, key=sectors.get) if sectors else None
    return sectors, primary


def _sector_question_result(state):
    return {
        "done": False,
        "question_number": len(state["answers"]) + 1,
        "total_questions": SECTOR_QUESTIONS,
        "question": state["current"],
        "next_step": "Ask the student exactly this question, then call sector_quiz with their answer.",
    }


@chat_function(
    "sector_quiz",
    "Run the Career Discovery quiz: playful questions that never mention careers or school, ending with the "
    "student's best-fit career sectors (with percentages) and hidden strengths. Call with no arguments to "
    "start, then once per answer. Ask the student each question exactly as returned.",
    {"properties": {
        "answer": {"type": "string", "description": "The student's answer to the current question"},
        "finish_now": {"type": "boolean", "description": f"End early and get results (needs at least {SECTOR_MIN_TO_FINISH} answers)"},
        "restart": {"type": "boolean", "description": "Throw away progress and start again"}}},
    uses_session=True,
)
def sector_quiz(user_id, session, answer=None, finish_now=False, restart=False):
    state = session.get("sector_quiz")
    if restart or state is None or state.get("done"):
        state = {"answers": [], "current": None, "done": False}
        session["sector_quiz"] = state
        state["current"] = _next_sector_question(state["answers"], user_id)
        return _sector_question_result(state)

    if answer is None or not str(answer).strip():
        return _sector_question_result(state)

    state["answers"].append({"number": len(state["answers"]) + 1, "question": state["current"],
                             "answer": str(answer).strip()})
    count = len(state["answers"])
    if count >= SECTOR_QUESTIONS or (finish_now and count >= SECTOR_MIN_TO_FINISH):
        report = _sector_report(state["answers"], user_id)
        sectors, primary = parse_sectors(report)
        state["done"] = True
        result = {"done": True, "questions_answered": count, "sectors": sectors, "primary_sector": primary,
                  "report_markdown": report}
        session["last_sector_result"] = result
        return result
    state["current"] = _next_sector_question(state["answers"], user_id)
    return _sector_question_result(state)


@chat_function(
    "save_sector_result",
    "Save the student's finished Career Discovery quiz result to their account.",
    saves=True,
    uses_session=True,
)
def save_sector_result(user_id, session):
    from utils import database

    result = session.get("last_sector_result")
    if not result:
        return {"saved": False, "error": "There is no finished sector quiz to save. Run the sector quiz first."}
    sector = result["primary_sector"] or "Career Discovery"
    sectors = result["sectors"]
    database.save_report(
        user_id=user_id,
        report_type="career_quiz",
        title=f"Career Quiz - {sector} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=result["report_markdown"],
        cv_data={
            "recommended_sector": result["primary_sector"],
            "recommended_sectors": sectors,
            "sectors_display": ", ".join(f"{s} ({p}%)" for s, p in sectors.items()),
        },
    )
    return {"saved": True, "primary_sector": result["primary_sector"]}


# ---- degree quiz --------------------------------------------------------------

DEGREE_MIN_QUESTIONS = 3
DEGREE_MAX_QUESTIONS = 15
DEGREE_RESULTS = 3
_TRAILING_PARENS = re.compile(r"\s*\([^)]*\)\s*$")


def degree_names(df=None):
    """Distinct degree names in the DGES table (variants like '(Ensino em Inglês)' folded in)."""
    df = load_dges_df() if df is None else df
    if df is None or df.empty:
        return []
    names = {_TRAILING_PARENS.sub("", str(n)).strip() for n in df["course_name"].dropna()}
    return sorted(n for n in names if n)


def _pick_candidates(field, names, user_id):
    prompt = f"""TASK: SELECT_DEGREES

A student in Portugal is interested in this field: "{field}"

Here are all the degree names offered in Portugal, one per line:
{chr(10).join(names)}

Return ONLY a JSON array with the degree names (copied exactly as written above) that belong to this field
or are closely related to it. Include every real match, but no unrelated degrees."""
    picked = _parse_json(_ask(prompt, "Return only a JSON array of strings.", 0.2, "degree_quiz_candidates", user_id))
    valid = set(names)
    out = []
    for name in picked if isinstance(picked, list) else []:
        if name in valid and name not in out:
            out.append(name)
    return out


def _history(state):
    return "\n".join(f"Q{i}: {h['question']}\nA: {h['answer']}" for i, h in enumerate(state["history"], 1)) or "(none yet)"


def _next_degree_question(state, user_id):
    prompt = f"""TASK: NEXT_QUESTION

A student is exploring the field "{state['field']}". These degrees are still possible:
{chr(10).join(state['remaining'])}

Questions already asked, with answers:
{_history(state)}

Write the NEXT question. It must:
- be about what the student enjoys, wants to do day to day, or how they like to work (never name a degree)
- be easy to answer in a few words, ideally a choice between two things
- split the remaining degrees as evenly as it can, so the answer rules some of them out
- not repeat or rephrase an earlier question
- be under 20 words

Return ONLY JSON like {{"question": "..."}}"""
    data = _parse_json(_ask(prompt, "Return only JSON.", 0.6, "degree_quiz_question", user_id))
    question = str(data.get("question", "")).strip() if isinstance(data, dict) else ""
    if not question:
        raise ValueError("No question came back")
    return question


def _eliminate(state, answer, user_id):
    """Rule out degrees the answer makes unlikely, always keeping at least 3."""
    prompt = f"""TASK: ELIMINATE

Field: "{state['field']}"
Degrees still possible:
{chr(10).join(state['remaining'])}

Question: {state['current']}
Student's answer: {answer}

Which of the remaining degrees does this answer make a poor fit? Only name degrees that clearly don't match
what the student said. If the answer doesn't rule anything out, return an empty list.

Return ONLY JSON like {{"eliminate": ["Degree name", ...]}} using names copied exactly from the list."""
    try:
        data = _parse_json(_ask(prompt, "Return only JSON.", 0.2, "degree_quiz_eliminate", user_id))
        names = data.get("eliminate", []) if isinstance(data, dict) else []
    except Exception:
        names = []
    remaining = set(state["remaining"])
    out = []
    for n in names:
        if n in remaining and n not in out:
            out.append(n)
    out = out[: max(0, len(state["remaining"]) - DEGREE_RESULTS)]
    state["remaining"] = [d for d in state["remaining"] if d not in out]
    return out


def _final_picks(state, user_id):
    remaining = state["remaining"]
    prompt = f"""TASK: FINAL_PICK

Field: "{state['field']}"
Degrees left:
{chr(10).join(remaining)}

The student's answers:
{_history(state)}

Choose the {DEGREE_RESULTS} degrees that fit this student best, best first, and give each a one-sentence reason
that refers to what the student said. Use names copied exactly from the list.

Return ONLY JSON like {{"top": [{{"degree": "...", "reason": "..."}}]}}"""
    picks = []
    try:
        data = _parse_json(_ask(prompt, "Return only JSON.", 0.3, "degree_quiz_final", user_id))
        for item in data.get("top", []) if isinstance(data, dict) else []:
            name = item.get("degree") if isinstance(item, dict) else None
            if name in remaining and name not in [p["degree"] for p in picks]:
                picks.append({"degree": name, "reason": str(item.get("reason", "")).strip()})
    except Exception:
        pass
    for name in remaining:  # pad if the AI gave fewer than 3 valid ones
        if len(picks) >= DEGREE_RESULTS:
            break
        if name not in [p["degree"] for p in picks]:
            picks.append({"degree": name, "reason": ""})
    return picks[:DEGREE_RESULTS]


def _degree_question_result(state, excluded=None):
    out = {
        "done": False,
        "question_number": len(state["history"]) + 1,
        "max_questions": DEGREE_MAX_QUESTIONS,
        "degrees_still_possible": len(state["remaining"]),
        "question": state["current"],
        "next_step": "Ask the student exactly this question, then call degree_quiz with their answer.",
    }
    if excluded:
        out["just_ruled_out"] = excluded
    return out


def _degree_finish(state, session, user_id, excluded=None):
    picks = _final_picks(state, user_id)
    state["done"] = True
    result = {"done": True, "field": state["field"], "questions_asked": len(state["history"]),
              "top_degrees": picks}
    if excluded:
        result["just_ruled_out"] = excluded
    session["last_degree_result"] = result
    return result


@chat_function(
    "degree_quiz",
    "Run the degree quiz for a field the student names (e.g. 'computer science'). It asks 3 to 15 questions, "
    "each answer rules out some degrees offered in Portugal, and it ends with the 3 best-fitting degrees. "
    "Call with field to start, then once per answer. Ask each question exactly as returned.",
    {"properties": {
        "field": {"type": "string", "description": "The field or sector to explore; needed to start"},
        "answer": {"type": "string", "description": "The student's answer to the current question"},
        "restart": {"type": "boolean", "description": "Throw away progress and start again"}}},
    uses_session=True,
)
def degree_quiz(user_id, session, field=None, answer=None, restart=False):
    state = session.get("degree_quiz")
    wants_new = restart or state is None or state.get("done") or (
        field and state["field"].strip().lower() != field.strip().lower())
    if wants_new:
        if not field or not field.strip():
            return {"done": False, "error": "Ask the student which field they want to explore, then call again with field."}
        names = degree_names()
        candidates = _pick_candidates(field.strip(), names, user_id)
        if len(candidates) < DEGREE_RESULTS:
            return {"done": False, "error": f"Only {len(candidates)} degree(s) matched '{field}'. "
                                            "Try a broader field, or search those degrees directly."}
        state = {"field": field.strip(), "remaining": candidates, "history": [], "current": None, "done": False}
        session["degree_quiz"] = state
        if len(candidates) <= DEGREE_RESULTS:
            return _degree_finish(state, session, user_id)
        state["current"] = _next_degree_question(state, user_id)
        return _degree_question_result(state)

    if answer is None or not str(answer).strip():
        return _degree_question_result(state)

    answer = str(answer).strip()
    excluded = _eliminate(state, answer, user_id)
    state["history"].append({"question": state["current"], "answer": answer})
    asked = len(state["history"])
    if len(state["remaining"]) <= DEGREE_RESULTS or asked >= DEGREE_MAX_QUESTIONS:
        return _degree_finish(state, session, user_id, excluded)
    state["current"] = _next_degree_question(state, user_id)
    return _degree_question_result(state, excluded)


@chat_function(
    "save_degree_results",
    "Save the student's finished degree quiz result (their top 3 degrees) to their account.",
    saves=True,
    uses_session=True,
)
def save_degree_results(user_id, session):
    from utils import database

    result = session.get("last_degree_result")
    if not result:
        return {"saved": False, "error": "There is no finished degree quiz to save. Run the degree quiz first."}
    degrees = [p["degree"] for p in result["top_degrees"]]
    lines = ["# Degree Quiz Results", "", f"Field: {result['field']}", ""]
    for i, p in enumerate(result["top_degrees"], 1):
        lines += [f"### {i}. {p['degree']} (Top match)", "", p["reason"], ""]
    database.save_report(
        user_id=user_id,
        report_type="degree",
        title=f"Degree Quiz - {result['field']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content="\n".join(lines),
        cv_data={"degrees": degrees, "field": result["field"]},
    )
    return {"saved": True, "degrees": degrees}
