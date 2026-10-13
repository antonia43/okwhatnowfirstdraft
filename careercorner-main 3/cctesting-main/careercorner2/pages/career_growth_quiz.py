import os
import json
import streamlit as st
from dotenv import load_dotenv
from utils.database import save_report
from datetime import datetime
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id


load_dotenv()

QUIZ_GEMINI = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)


def render_career_growth_quiz():
    if "quiz_result" not in st.session_state:
        st.session_state.quiz_result = {}
    st.markdown('<div class="cc-page-active">', unsafe_allow_html=True)
    st.header("↗ Career Growth Quiz")
    st.markdown('</div>', unsafe_allow_html=True)

    has_cv_data = bool(st.session_state.get("cv_data"))
    if "quiz_mode" not in st.session_state:
        st.session_state.quiz_mode = None
    
    if st.session_state.get("quiz_started") and not st.session_state.get("quiz_final_report"):
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← Restart", width='stretch', key="restart_quiz_btn"):
                st.session_state.quiz_mode = None
                _reset_quiz_state()
                st.rerun()
        st.divider()

    # back to mode chooser
    if st.session_state.quiz_mode in ("with_cv", "no_cv") and not st.session_state.get("quiz_started"):
        if st.button("← Back to options", width='stretch'):
            st.session_state.quiz_mode = None
            _reset_quiz_state()
            st.rerun()

    # decide mode
    if st.session_state.quiz_mode is None:
        if has_cv_data:
            st.info("✓ CV detected! Choose how to proceed:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Use my CV", width='stretch', type="primary"):
                    st.session_state.quiz_mode = "with_cv"
                    _reset_quiz_state()
                    st.rerun()
            with col2:
                if st.button("⃠ Continue without CV", width='stretch'):
                    st.session_state.quiz_mode = "no_cv"
                    _reset_quiz_state()
                    st.rerun()
            
            st.divider()
            st.caption("✂ Or prepare your CV first:")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Analyze existing CV", width='stretch'):
                    st.session_state.redirect_to = "CV Analysis"
                    st.rerun()
            with col4:
                if st.button("✐ Build / Enhance CV", width='stretch'):
                    st.session_state.redirect_to = "CV Builder"
                    st.rerun()
        else:
            st.info(
                "You can: **(1)** continue without a CV, "
                "**(2)** analyze an existing CV first, or "
                "**(3)** build a new CV from scratch."
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⃠ Continue without a CV", width='stretch', type="primary"):
                    st.session_state.quiz_mode = "no_cv"
                    _reset_quiz_state()
                    st.rerun()

            with col2:
                if st.button("✓ I already have a CV", width='stretch'):
                    st.session_state.redirect_to = "CV Analysis"
                    st.session_state.quiz_mode = None
                    st.rerun()

            with col3:
                if st.button("✐ Build my CV", width='stretch'):
                    st.session_state.redirect_to = "CV Builder"
                    st.session_state.quiz_mode = None
                    st.rerun()

        if st.session_state.quiz_mode is None:
            return

    # if user chose CV mode but has none yet
    if st.session_state.quiz_mode == "with_cv" and not has_cv_data:
        st.warning("To personalize this quiz, please complete your CV Analysis first.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩ Go to CV Analysis", width='stretch', type="primary"):
                st.session_state.redirect_to = "CV Analysis"
                st.stop()
        with col2:
            if st.button("⃠ Continue without a CV instead", width='stretch'):
                st.session_state.quiz_mode = "no_cv"
                _reset_quiz_state()
                st.rerun()
        return

    if st.session_state.quiz_mode == "with_cv":
        st.success("✓ Using your CV to design personalized questions.")
    else:
        st.info("✓ Running quiz without a CV – questions are more general about how you like to work.")

    # initialising quiz state
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "quiz_phase" not in st.session_state:
        st.session_state.quiz_phase = 1
    if "experience_questions" not in st.session_state:
        st.session_state.experience_questions = []
    if "experience_answers" not in st.session_state:
        st.session_state.experience_answers = {}
    if "softskills_questions" not in st.session_state:
        st.session_state.softskills_questions = []
    if "softskills_answers" not in st.session_state:
        st.session_state.softskills_answers = {}
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "quiz_final_report" not in st.session_state:
        st.session_state.quiz_final_report = None

    if not st.session_state.quiz_started:
        _render_quiz_intro()
    elif st.session_state.quiz_final_report:
        _render_final_report()
    else:
        _render_quiz_questions()


def _reset_quiz_state():
    for key in [
        "quiz_started",
        "quiz_phase",
        "experience_questions",
        "experience_answers",
        "softskills_questions",
        "softskills_answers",
        "current_question_index",
        "quiz_final_report",
    ]:
        st.session_state.pop(key, None)

def _render_quiz_intro():
    st.markdown("---")
    st.subheader("How it works:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            **Part 1 – Experience & Preferences**  
            AI asks questions about what you enjoy and dislike in work:
            - People vs technical tasks  
            - Pressure vs calm  
            - Routine vs variety
            """
        )
    with col2:
        st.markdown(
            """
            **Part 2 – Soft Skills**  
            Questions adapt to your previous answers and explore:
            - Leadership & communication  
            - Problem‑solving style  
            - Adaptability & learning
            """
        )

    mode = st.session_state.get("quiz_mode", "no_cv")
    if mode == "with_cv":
        st.caption("We'll use your CV to make the questions feel specific to your experience.")
    else:
        st.caption("No CV? We'll still create a curated quiz based only on your answers here.")

    st.markdown("---")
    if st.button("⟡ Start Career Growth Quiz", width='stretch', type="primary"):
        st.session_state.quiz_started = True
        _generate_experience_questions()
        st.rerun()

def _generate_experience_questions():
    mode = st.session_state.quiz_mode
    if mode == "with_cv":
        cv = st.session_state.cv_data
        context = f"Experience summary: {cv.get('experience_summary', '')}\nSkills: {cv.get('skills', '')}"
    else:
        context = "No CV. Assume early‑career or transitioning person; ask about preferred tasks and environments."

    prompt = f"""
You are a career assessment designer.

Context:
{context}

Design 6 questions (mix sliders and multiple‑choice) to discover:
- what they enjoy vs dislike at work
- people vs technical preferences
- pressure vs calm environments
- teamwork vs independence
- structure vs creativity
- routine vs variety

Rules:
- Make questions concrete and easy to answer.
- Personalize using the context when available.
- Return ONLY valid JSON:

{{
  "questions": [
    {{
      "question": "text",
      "aspect": "short_tag",
      "type": "slider" or "multiple_choice",
      "scale": {{"0": "...", "50": "...", "100": "..."}}  # if slider
      "options": ["..."]                                   # if multiple_choice
    }},
    ...
  ]
}}
"""

    try:
        with st.spinner("Generating personalized questions..."):
            text = QUIZ_GEMINI.generate_content(
                prompt=prompt,
                system_instruction=(
                "You are a career assessment designer. "
                "Return ONLY valid JSON with key 'questions'."
                ),
                temperature=0.3,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )
            text = text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")

            data = json.loads(text)
            st.session_state.experience_questions = data.get("questions", [])
    except Exception as e:
        st.error(f"Error generating questions, using fallback. ({e})")
        st.session_state.experience_questions = _fallback_experience_questions()

def _fallback_experience_questions():
    return [
        {
            "question": "How much do you enjoy working under pressure and tight deadlines?",
            "aspect": "pressure",
            "type": "slider",
            "scale": {"0": "Very stressful", "50": "OK", "100": "I thrive on it"},
        },
        {
            "question": "What kind of tasks do you usually enjoy more?",
            "aspect": "task_type",
            "type": "multiple_choice",
            "options": [
                "Working with people",
                "Analytical/technical tasks",
                "Creative work",
                "Organizing and planning",
                "Hands‑on/manual work",
            ],
        },
        {
            "question": "How comfortable are you with customer or client interaction?",
            "aspect": "customer",
            "type": "slider",
            "scale": {"0": "Very uncomfortable", "50": "Neutral", "100": "Really enjoy it"},
        },
        {
            "question": "What do you usually dislike most in a job or project?",
            "aspect": "dislikes",
            "type": "multiple_choice",
            "options": [
                "Repetitive tasks",
                "Lack of autonomy",
                "Too much pressure",
                "Poor work‑life balance",
                "Unclear expectations",
            ],
        },
        {
            "question": "How much do you prefer teamwork vs. working independently?",
            "aspect": "teamwork",
            "type": "slider",
            "scale": {"0": "Mostly alone", "50": "Balanced", "100": "Mostly in teams"},
        },
        {
            "question": "What kind of environment do you imagine yourself in?",
            "aspect": "environment",
            "type": "multiple_choice",
            "options": [
                "Fast‑paced startup",
                "Structured corporate",
                "Remote/flexible",
                "Creative studio",
                "Research/academic",
            ],
        },
    ]

def _render_quiz_questions():
    if st.session_state.quiz_phase == 1:
        questions = st.session_state.experience_questions
        phase_name = "Part 1 – Experience & Preferences"
    else:
        if not st.session_state.softskills_questions:
            _generate_softskills_questions()
        questions = st.session_state.softskills_questions
        phase_name = "Part 2 – Soft Skills"

    total = len(questions)
    idx = st.session_state.current_question_index

    if idx >= total:
        if st.session_state.quiz_phase == 1:
            st.session_state.quiz_phase = 2
            st.session_state.current_question_index = 0
            _generate_softskills_questions()
            st.rerun()
        else:
            _generate_final_report()
            st.rerun()
        return

    q = questions[idx]
    q_text = q["question"]
    q_type = q["type"]
    answer_key = f"q{st.session_state.quiz_phase}_{idx}"

    st.markdown(f"### {phase_name}")
    st.progress((idx + 1) / total)
    st.caption(f"Question {idx + 1} of {total}")
    st.markdown("---")
    st.subheader(q_text)

    answer = None

    if q_type == "slider":
        scale = q.get("scale", {"0": "Low", "50": "Medium", "100": "High"})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<p style='text-align:left'>{scale['0']}</p>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<p style='text-align:center'>{scale['50']}</p>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<p style='text-align:right'>{scale['100']}</p>", unsafe_allow_html=True)

        answer = st.slider(
            "Your response",
            0,
            100,
            50,
            10,
            key=f"slider_{answer_key}",
            label_visibility="collapsed",
        )
    elif q_type == "multiple_choice":
        options = q.get("options", [])
        answer = st.radio(
            "Select one:",
            options,
            key=f"radio_{answer_key}",
        )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0 and st.button("← Back", width='stretch'):
            st.session_state.current_question_index -= 1
            st.rerun()
    with col2:
        if st.button("Next →", width='stretch', type="primary"):
            if q_type == "slider":
                answer = st.session_state.get(f"slider_{answer_key}")
            if answer is None and answer != 0:
                st.warning("Please answer before continuing.")
                return

            store = (
                st.session_state.experience_answers
                if st.session_state.quiz_phase == 1
                else st.session_state.softskills_answers
            )
            store[idx] = {
                "question": q_text,
                "answer": answer,
                "aspect": q.get("aspect", "unknown"),
            }
            st.session_state.current_question_index += 1
            st.rerun()

def _generate_softskills_questions():
    exp_answers = st.session_state.experience_answers

    prompt = f"""
You are designing the SECOND part of a career‑growth quiz.

Previous answers:
{json.dumps(exp_answers, indent=2)}

Generate 6 new questions that explore soft skills:
- leadership vs individual contributor
- communication style
- problem‑solving approach
- adaptability and learning
- stress management
- collaboration style

Rules:
- Use the previous answers to tailor the questions.
- Mix sliders and multiple‑choice.
- Do NOT repeat earlier questions.
- Return ONLY JSON with key "questions".
"""

    try:
        with st.spinner("Generating soft‑skills questions..."):
            text = QUIZ_GEMINI.generate_content(
                prompt=prompt,
                system_instruction=(
                    "You are a career assessment designer. "
                    "Return ONLY valid JSON with key 'questions'."
                ),
                temperature=0.3,
                user_id=get_user_id(),
                session_id=get_session_id(),
            ).strip()

            if text.startswith("```json"):
                text = text.replace("``````", "").strip()
            data = json.loads(text)
            st.session_state.softskills_questions = data.get("questions", [])
    except Exception as e:
        st.error(f"Error generating soft‑skills questions, using fallback. ({e})")
        st.session_state.softskills_questions = _fallback_softskills_questions()

def _fallback_softskills_questions():
    return [
        {
            "question": "How comfortable are you in leadership roles?",
            "aspect": "leadership",
            "type": "slider",
            "scale": {"0": "Prefer to follow", "50": "Either is fine", "100": "Natural leader"},
        },
        {
            "question": "Which communication style do you prefer most?",
            "aspect": "communication",
            "type": "multiple_choice",
            "options": ["Face‑to‑face", "Written", "Presentations", "One‑on‑one", "Group discussions"],
        },
        {
            "question": "How do you usually react to unexpected changes?",
            "aspect": "adaptability",
            "type": "slider",
            "scale": {"0": "Very uncomfortable", "50": "I adapt with effort", "100": "I enjoy change"},
        },
        {
            "question": "How do you normally solve complex problems?",
            "aspect": "problem_solving",
            "type": "multiple_choice",
            "options": [
                "Data and analysis",
                "Creative brainstorming",
                "Asking others",
                "Trial and error",
                "Researching deeply",
            ],
        },
        {
            "question": "How well do you handle stressful situations?",
            "aspect": "stress",
            "type": "slider",
            "scale": {"0": "Easily overwhelmed", "50": "Manageable", "100": "Stay calm and focused"},
        },
        {
            "question": "How do you prefer to learn new skills?",
            "aspect": "learning",
            "type": "multiple_choice",
            "options": [
                "Hands‑on practice",
                "Reading",
                "Watching tutorials",
                "Mentoring",
                "Experimenting on my own",
            ],
        },
    ]

def _generate_final_report():
    cv_data = st.session_state.get("cv_data", {})
    exp = st.session_state.experience_answers
    soft = st.session_state.softskills_answers

    prompt = f"""
You are a senior career counselor.

Using this information:
CV data (may be empty): {json.dumps(cv_data, indent=2)}
Experience answers: {json.dumps(exp, indent=2)}
Soft‑skills answers: {json.dumps(soft, indent=2)}

Write a concise markdown report with:
- Career profile summary with **PRIMARY_SECTOR** (tech/business/healthcare/etc)
- 3–5 suggested career directions, each with 2–3 specific reasons
- Top 3 skills to develop next and concrete actions for the next 3 months.

At the TOP of your response, add: SECTOR: [one word sector]
"""

    try:
        with st.spinner("Generating your career growth report..."):
            text = QUIZ_GEMINI.generate_content(
                prompt=prompt,
                system_instruction=(
                    "You are a senior career counselor. "
                    "Return a concise markdown report starting with 'SECTOR: ...'."
                ),
                temperature=0.3,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )
            st.session_state.quiz_final_report = text
    except Exception as e:
        st.error(f"Error generating report: {e}")
        st.session_state.quiz_final_report = "There was an error generating your report."

def _render_final_report():
    st.markdown("---")
    st.header("Your Career Growth Report")
    st.markdown(st.session_state.quiz_final_report or "")

    report = st.session_state.quiz_final_report
    if report and "SECTOR:" in report:
        sector_line = report.split("SECTOR:")[1].split("\n")[0].strip()
        st.session_state.quiz_result["sector"] = sector_line

    # auto saving to database
    if "username" in st.session_state and st.session_state.username:
        if "quiz_saved" not in st.session_state:
            try:
                sector = st.session_state.quiz_result.get("sector", "General")
                
                save_report(
                    user_id=st.session_state.username,
                    report_type="professional_career_quiz",
                    title=f"Career Growth Quiz - {sector} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content=report,
                    cv_data=None
                )
                
                st.session_state.quiz_saved = True
                st.success("🗂️ Quiz results saved to My Reports!")
            except Exception as e:
                st.warning(f"Could not auto-save quiz: {e}")

    st.markdown("---")
    
    
    if report:
        st.download_button(
            "➜] Download Quiz Report (TXT)",
            data=report,
            file_name=f"career_quiz_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            width='stretch'
        )
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    def _restart():
        _reset_quiz_state()
        st.session_state.pop("quiz_saved", None)
        st.rerun()

    with col1:
        if st.button("↻ Retake Quiz", width='stretch', on_click=_restart):
            pass
    with col2:
        if st.button(" Improve my CV", width='stretch'):
            _reset_quiz_state()
            st.session_state.pop("quiz_saved", None)
            st.session_state.redirect_to = "CV Analysis"
            st.rerun()
    with col3:
        if st.button("→ Your Next Steps", width='stretch'):
            st.session_state.quiz_result = {
                "sector": st.session_state.quiz_result.get("sector", "generated_from_quiz"),
                "experience_answers": st.session_state.experience_answers,
                "softskills_answers": st.session_state.softskills_answers,
            }
            _reset_quiz_state()
            st.session_state.pop("quiz_saved", None)
            st.session_state.redirect_to = "Your Next Steps"
            st.rerun()
