import os
import json
import streamlit as st
from dotenv import load_dotenv
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
import tempfile
import os
import time
from pages.cv_analysis import _extract_structured_multimodal

load_dotenv()
INTERVIEW_GEMINI = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)

# ---------- State reset helpers ----------

def reset_interview_to_start():
    st.session_state.interview_mode = None
    st.session_state.interview_questions = []
    st.session_state.interview_answers = {}
    st.session_state.current_interview_q = 0
    st.session_state.interview_feedback = None


def render_interview_personalization():
    cv = st.session_state.get("cv_data")
    has_cv = bool(cv)

    col1, col2 = st.columns(2)

    with col1:
        if has_cv:
            use_cv = st.checkbox(
                "✓ Use my CV for personalized questions", 
                value=True,
                key="use_cv_for_interview"
            )
            
            if use_cv:
                st.success("Using your CV for personalization.")
                st.session_state.interview_cv = cv
            else:
                st.info("CV not being used - questions will be general.")
                st.session_state.interview_cv = {}
        else:
            st.info("No CV loaded – you can still continue with general questions.")
            st.session_state.interview_cv = {}
            
            if st.button("↩ Go to CV Analysis", width='stretch'):
                st.session_state.redirect_to = "CV Analysis"
                st.rerun()

    with col2:
        cover_file = st.file_uploader(
            "Upload a cover letter (optional)",
            type=["txt", "pdf", "docx"],
            key="cover_letter_file",
        )

    cover_text = ""
    if cover_file is not None:
        try:
            file_extension = cover_file.name.split(".")[-1].lower()
            
            if file_extension == "txt":
                cover_text = cover_file.read().decode("utf-8")
            
            elif file_extension in ["pdf", "docx"]:
                # Reuse CV extraction with simple schema
                result = _extract_structured_multimodal(
                    cover_file, 
                    schema={"text": "Extract all text from this document"}
                )
                
                if result.get("success"):
                    cover_text = result["data"].get("text", "")
                    if not cover_text.strip():
                        st.warning("PDF extracted but appears empty. Try a TXT file instead.")
                else:
                    st.error(f"Failed to extract PDF: {result.get('error', 'Unknown error')}")
                    cover_text = ""
            
            if cover_text.strip():
                st.success(f"✓ Loaded cover letter ({len(cover_text)} characters)")
                st.session_state.interview_cover = cover_text
                
                # Debug: show first 200 chars
                if st.session_state.get("debug_mode"):
                    with st.expander("Debug: Cover Letter Content"):
                        st.text(cover_text[:200] + "...")
            else:
                st.warning("Cover letter file was loaded but appears empty.")
                st.session_state.interview_cover = ""
            
        except Exception as e:
            st.error(f"⚠︎ Could not read cover letter: {e}")
            cover_text = ""
            st.session_state.interview_cover = ""

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("✍︎ Build / Improve my CV", width='stretch'):
            st.session_state.redirect_to = "CV Builder"
            st.rerun()
    with nav2:
        if st.button("✐ Build a Cover Letter", width='stretch'):
            st.session_state.redirect_to = "CV Builder"
            st.rerun()

def render_interview_simulator():
    st.header("🎤︎︎ Interview Simulator")
    st.session_state.debug_mode = False

    if "interview_mode" not in st.session_state:
        st.session_state.interview_mode = None
    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = []
    if "interview_answers" not in st.session_state:
        st.session_state.interview_answers = {}
    if "current_interview_q" not in st.session_state:
        st.session_state.current_interview_q = 0
    if "interview_feedback" not in st.session_state:
        st.session_state.interview_feedback = None

    if st.session_state.interview_mode is None and not st.session_state.interview_questions:
        render_interview_personalization()
        render_interview_menu()
    elif st.session_state.interview_feedback:
        render_interview_feedback()
    else:
        render_interview_questions()


def render_interview_menu():
    st.subheader("☘︎ Choose Your Interview Type:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            ### Quick Practice
            - Focused interview questions  
            - Tailored using your CV / cover letter if available  
            - Instant AI feedback on each answer  
            - ~10–15 minutes
        """)

        question_types = st.multiselect(
            "Focus areas:",
            ["Behavioral", "Technical", "Situational",
             "Strengths/Weaknesses", "Career Goals"],
            default=["Behavioral", "Strengths/Weaknesses"],
        )

        if st.button("⟡ Start Quick Practice", width='stretch'):
            
            st.session_state.interview_questions = [] # resetting
            st.session_state.current_interview_q = 0  # resetting index
            
            n = len(question_types)

            if n == 0:
                st.warning("Pick at least one focus area.")
                return
            elif n == 1:
                # 3 questions, all same category
                expanded_focus = question_types * 3
            elif n == 2:
                # 2 per area -> total 4
                expanded_focus = question_types * 2
            else:
                # 3 or more -> one per area
                expanded_focus = question_types

            generate_practice_questions(expanded_focus)
            st.session_state.interview_mode = "practice"
            st.rerun()

    with col2:
        st.markdown("""
            ### Mock Interview
            - Full interview simulation (10 questions)  
            - Tailored to target job/company + your CV/cover letter if available  
            - Comprehensive feedback report  
            - ~30 minutes
        """)

        target_role = st.text_input(
            "Target job title:", placeholder="e.g., Senior Software Engineer"
        )
        target_company = st.text_input(
            "Company (optional):", placeholder="e.g., Google"
        )

        if st.button("⟡ Start Mock Interview", width='stretch'):
            if target_role:
                generate_mock_questions(target_role, target_company)
                st.session_state.interview_mode = "mock"
                st.rerun()
            else:
                st.warning("Please enter a target job title")



def generate_practice_questions(focus_areas):
    cv_data = st.session_state.get("interview_cv") or {}
    cover_text = st.session_state.get("interview_cover") or ""
    
    # Debug output
    if st.session_state.get("debug_mode"):
        with st.expander("🔍 Debug: Prompt Inputs"):
            st.write(f"CV skills: {cv_data.get('skills', [])}")
            st.write(f"Cover text length: {len(cover_text)}")
            st.write(f"Cover text preview: {cover_text[:300] if cover_text else 'EMPTY'}")
            
    num_questions = len(focus_areas)

    category_rules = "\n".join(
        [f"- Question {i+1} MUST be '{cat}'" for i, cat in enumerate(focus_areas)]
    )

    prompt = f"""Generate EXACTLY {num_questions} interview questions - ONE PER focus area: {', '.join(focus_areas)}.

IMPORTANT: 
{category_rules}
- ONLY use these categories, no others.
- Match the EXACT order above.

Candidate background (OPTIONAL): 
CV Skills: {cv_data.get('skills', [])}
Cover: {cover_text[:500]}

Return ONLY valid JSON:
{{
  "questions": [
    {{"question": "QUESTION TEXT", "category": "EXACT CATEGORY NAME", "tips": "brief tip"}}
  ]
}}
"""

    try:
        with st.spinner("Generating practice questions..."):
            response = INTERVIEW_GEMINI.generate_content(
                prompt=prompt,
                system_instruction="Generate realistic interview questions. Return ONLY valid JSON.",
                temperature=0.5,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )

            response_text = response.strip()
            response_text = (
                response_text.replace("```", "")
                .strip()
            )

            # grabbing json slice
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                candidate = response_text[start:end]
            else:
                candidate = response_text

            data = json.loads(candidate)
            raw_questions = data.get("questions", []) or []

            fixed_questions = []
            for i in range(num_questions):
                q_src = raw_questions[i] if i < len(raw_questions) else {}
                fixed_questions.append(
                    {
                        "question": (q_src.get("question") or "").strip()
                        or f"Custom {focus_areas[i]} interview question {i+1}.",
                        "category": focus_areas[i],
                        "tips": q_src.get("tips", ""),
                    }
                )

            st.session_state.interview_questions = fixed_questions

    except Exception as e:
        st.error(f"Error reading AI questions, using defaults instead.\n\n{e}")
        st.session_state.interview_questions = get_fallback_questions()


def generate_mock_questions(role, company):
    cv_data = st.session_state.get("interview_cv") or {}
    cover_text = st.session_state.get("interview_cover") or ""
    company_context = f" at {company}" if company else ""

    prompt = f"""Generate 10 interview questions for a {role}{company_context} position.

Candidate's background (may be partial):
Work Experience: {cv_data.get('work_experience', [])}
Skills: {cv_data.get('skills', [])}
Education: {cv_data.get('education', [])}
Cover Letter: {cover_text}

Generate a realistic interview covering:
1. Introduction/Background (1–2 questions)
2. Behavioral questions (3–4 questions)
3. Technical/Role-specific (2–3 questions)
4. Situational (2 questions)
5. Closing questions (1 question)

Return ONLY JSON with question, category, and tips for each.
"""

    try:
        with st.spinner(f"Preparing mock interview for {role}..."):
            response = INTERVIEW_GEMINI.generate_content(
                prompt=prompt,
                system_instruction=(
                    "Generate realistic, role-specific interview questions. "
                    "Return ONLY valid JSON with shape "
                    '{"questions":[{"question":"...","category":"...","tips":"..."}]}.'
                ),
                temperature=0.5,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )

            response_text = response.strip()
            response_text = (
                response_text.replace("```", "")
                .strip()
            )

            # grabbing json slice
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                candidate = response_text[start:end]
            else:
                candidate = response_text

            data = json.loads(candidate)
            raw_questions = data.get("questions", []) or []

            questions = []

            for q in raw_questions[:10]:
                text = (q.get("question") or "").strip()
                if not text:
                    continue
                questions.append(
                    {
                        "question": text,
                        "category": q.get("category", "General"),
                        "tips": q.get("tips", ""),
                    }
                )

            while len(questions) < 10:
                i = len(questions)
                questions.append(
                    {
                        "question": f"[Extra] Question {i+1} for {role}.",
                        "category": "General",
                        "tips": "",
                    }
                )

            st.session_state.interview_questions = questions

    except Exception as e:
        st.error(f"Error reading mock questions, using defaults instead.\n\n{e}")
        st.session_state.interview_questions = get_fallback_questions()


def get_fallback_questions():
    return [
        {
            "question": "Tell me about yourself and your background.",
            "category": "Introduction",
            "tips": "Keep it to 2–3 minutes, focus on relevant experience.",
        },
        {
            "question": "Tell me about a time you faced a significant challenge at work. How did you handle it?",
            "category": "Behavioral",
            "tips": "Use the STAR method.",
        },
        {
            "question": "What are your greatest strengths?",
            "category": "Strengths/Weaknesses",
            "tips": "Pick 2–3 relevant strengths with examples.",
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "category": "Career Goals",
            "tips": "Show ambition but be realistic.",
        },
        {
            "question": "Why do you want to work here?",
            "category": "Company Fit",
            "tips": "Research the company and be specific.",
        },
    ]


def render_interview_questions():
    if st.button("← Back to interview setup"):
        reset_interview_to_start()
        st.rerun()

    questions = st.session_state.interview_questions
    current_q = st.session_state.current_interview_q

    if current_q >= len(questions):
        generate_interview_feedback()
        st.rerun()
        return

    progress = (current_q + 1) / len(questions)
    st.progress(progress)
    st.caption(f"Question {current_q + 1} of {len(questions)}")
    st.markdown("---")

    q_data = questions[current_q]
    st.subheader(q_data["question"])
    st.caption(f"☑ Category: {q_data['category']}")

    st.markdown("<br>", unsafe_allow_html=True)

    answer = st.text_area(
        "Your answer:",
        height=200,
        placeholder="Type your answer here...",
        key=f"answer_{current_q}",
    )

    col1, col2, _ = st.columns([2, 1, 1])
    with col1:
        st.caption("ⓘ Tip: Aim for 1–3 minutes per answer.")

    st.markdown("---")
    nav1, nav2, nav3 = st.columns([1, 1, 3])

    with nav1:
        if current_q > 0:
            if st.button("← Previous", width='stretch'):
                st.session_state.current_interview_q -= 1
                st.rerun()

    with nav2:
        if st.button("Skip ↷", width='stretch'):
            st.session_state.current_interview_q += 1
            st.rerun()

    with nav3:
        if st.button("Next →", width='stretch', type="primary"):
            if answer.strip():
                st.session_state.interview_answers[current_q] = {
                    "question": q_data["question"],
                    "category": q_data["category"],
                    "answer": answer,
                }
                st.session_state.current_interview_q += 1
                st.rerun()
            else:
                st.warning("Please provide a text answer before continuing!")


def generate_interview_feedback():
    answers = st.session_state.interview_answers
    cv_data = st.session_state.get("interview_cv") or {}
    cover_text = st.session_state.get("interview_cover") or ""

    prompt = f"""Analyze this interview performance and provide detailed feedback.

CV data (may be empty): {cv_data}
Cover letter (may be empty): {cover_text}

Interview Answers:
{answers}

Provide:
1. Overall Performance Score (1–10)
2. Strengths
3. Areas for Improvement (specific per answer)
4. Best Answer and why
5. Answer That Needs Work and how to fix it
6. Key Takeaways (3–5 actionable tips)
7. Recommended Practice (what to focus on next)

Be constructive, specific, and encouraging. Use markdown formatting.
"""

    try:
        with st.spinner("Analyzing your interview performance..."):
            feedback = INTERVIEW_GEMINI.generate_content(
                prompt=prompt,
                system_instruction="You are an experienced interview coach providing constructive feedback.",
                temperature=0.6,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )
            st.session_state.interview_feedback = feedback
    except Exception as e:
        st.error(f"Error: {e}")

def render_interview_feedback():
    if st.button("← Back to interview setup"):
        reset_interview_to_start()
        st.rerun()

    st.markdown("---")
    st.header("🗂️ Interview Feedback Report")

    feedback = st.session_state.interview_feedback
    st.markdown(feedback)

    st.markdown("---")
    st.subheader("What's next?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⟳ Practice Again", width='stretch'):
            reset_interview_to_start()
            st.rerun()

    with col2:
        if st.button("✍︎ Update CV", width='stretch'):
            reset_interview_to_start()
            st.session_state.redirect_to = "CV Analysis"
            st.rerun()

    with col3:
        if st.button("☑ Career Growth Quiz", width='stretch'):
            reset_interview_to_start()
            st.session_state.redirect_to = "Career Growth"
            st.rerun()
