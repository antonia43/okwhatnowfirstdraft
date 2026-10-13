

import streamlit as st
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
from utils.database import save_report, load_user_quiz
from datetime import datetime
import os
import re
from dotenv import load_dotenv
import json

def _sector_with_other(label: str, key_prefix: str, default: str | None = None):
    options = ["Technology", "Healthcare", "Business", "Engineering", "Creative", "Other"]
    sector = st.selectbox(
        label,
        options,
        key=f"{key_prefix}_select",
        index=options.index(default) if default in options else 0,
    )

    if sector == "Other":
        custom = st.text_input(
            "Type the area you're interested in:",
            key=f"{key_prefix}_other",
            placeholder="e.g., Game Design, Environmental Science, Fashion...",
        )
        if custom.strip():
            sector = custom.strip()

    return sector


def render_degree_picker():
    st.header("Interactive Degree Picker")

    # step 1 is picking portuguese or international
    if "degree_region" not in st.session_state:
        st.session_state.degree_region = None

    if st.session_state.degree_region is None:
        st.info("**First: Choose your profile**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🇵🇹 Portuguese Student", width='stretch', type="primary"):
                st.session_state.degree_region = "Portugal"
                st.rerun()
            st.caption("Portuguese: Only DGES degrees in Portugal")
        with col2:
            if st.button("🌎 International Student", width='stretch'):
                st.session_state.degree_region = "International"
                st.rerun()
            st.caption("International: Global universities and programs")


        return

    # showing selected profile
    region_label = (
        "Portuguese Student (DGES only)"
        if st.session_state.degree_region == "Portugal"
        else "International Student"
    )
    st.success(f"✓ Profile: **{region_label}**")
    if st.button("↺ Change Profile", key="change_region_btn"):
        st.session_state.degree_region = None
        reset_degree_picker()
        st.rerun()

    st.divider()

    if "use_manual_sector" not in st.session_state:
        st.session_state.use_manual_sector = False


    # loading career quiz reports from database
    user_id = get_user_id()
    
    # 1) Check session_state first (same-session use)
    sectors_dict = st.session_state.get("recommended_sectors")
    primary_sector = st.session_state.get("recommended_sector")
    sectors_display = st.session_state.get("sectors_display")  # ← Add this line

        # 2) If not in session, load from DB (after logout/login)
    if not sectors_dict and not primary_sector:
        from utils.database import load_career_quiz_metadata
        quiz_result = load_career_quiz_metadata(user_id)

    
    # 3) Display sector selection if we have data
    if sectors_dict:
        display_options = [f"{s} ({p}%)" for s, p in sectors_dict.items()]
        selected_display = st.selectbox(
            "Sectors from your Career Discovery Quiz:",
            display_options,
            key="quiz_sector_select",
        )
        sector = selected_display.split(" (")[0]
        st.session_state.recommended_sector = sector
        st.session_state.recommended_sectors = sectors_dict
        st.session_state.sectors_display = sectors_display  # Now it's always defined
    elif primary_sector:
        sector = primary_sector
        st.info(f"Using Career Quiz sector: **{sector}**")
        st.session_state.recommended_sector = sector
    else:
        # Manual fallback if no quiz data
        st.info("Select your sector of interest")
        sector = _sector_with_other("Interested in:", "manual_noquiz")
        st.session_state.recommended_sector = sector

    st.write("Answer 5–7 yes/no questions → get a personalized degree report!")

    # initializing session state
    for key in [
        "degree_picker_active",
        "degree_questions",
        "degree_answers",
        "degree_question_count",
        "degree_conversation_history",
        "degree_final_report",
    ]:
        if key not in st.session_state:
            if key == "degree_picker_active":
                st.session_state[key] = False
            elif key in ["degree_questions", "degree_conversation_history"]:
                st.session_state[key] = []
            else:
                st.session_state[key] = {}

    if not st.session_state.degree_picker_active:
        st.markdown("---")
        st.subheader("How it works:")
        st.write("• 5–7 strict yes/no questions")
        st.write("• Personalized degrees + pros/cons")
        if st.session_state.degree_region == "Portugal":
            st.write("• **Only DGES-accredited Portuguese degrees**")
        else:
            st.write("• Global degree recommendations")
        st.write("• Auto-saved to My Reports")

        if st.button("⋆ Start Session", width='stretch', type="primary"):
            st.session_state.degree_picker_active = True
            st.session_state.degree_question_count = 0
            st.session_state.degree_answers = {}
            st.session_state.degree_conversation_history = []
            st.session_state.degree_final_report = None
            st.session_state.degree_report_saved = False
            st.rerun()
    else:
        render_interactive_questions(st.session_state.recommended_sector)


def render_interactive_questions(sector):
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY missing")
        return

    gemini_client = LangfuseGeminiWrapper(api_key=api_key, model="gemini-2.5-flash")
    user_id = get_user_id()
    session_id = get_session_id()

    MAX_QUESTIONS = 7
    if st.session_state.degree_question_count >= MAX_QUESTIONS:
        generate_final_report(gemini_client, sector, user_id, session_id)
        return

    st.markdown("---")
    st.progress(st.session_state.degree_question_count / MAX_QUESTIONS)
    st.subheader(f"Q{st.session_state.degree_question_count + 1}/{MAX_QUESTIONS}")

    for msg in st.session_state.degree_conversation_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if (
        len(st.session_state.degree_conversation_history) == 0
        or st.session_state.degree_conversation_history[-1]["role"] == "user"
    ):
        answer_context = "\n".join(
            [f"Q: {q}\nA: {a}" for q, a in st.session_state.degree_answers.items()]
        )
        grades_context = (
            f"\nGrades: {st.session_state.get('grades_data', 'N/A')}"
            if "grades_data" in st.session_state
            else ""
        )

        region = st.session_state.get("degree_region", "International")

        system_instruction = f"""
You are generating ONE short yes/no question for a high‑school student who is choosing a degree.

HARD RULES (MUST OBEY ALL):
- Output ONLY a single question, nothing else.
- Max 15 words.
- The question must be answerable with Yes or No alone.
- Do NOT use the word "or".
- Do NOT compare two options (no "X or Y", no "more A than B").
- Single clause only (avoid multiple commas / 'and').
- Do NOT ask fact questions with an objectively correct answer
  (no trivia like "Is X only used for Y?").

CONTENT RULES (MUST OBEY ALL):
- The question must reveal a PREFERENCE that helps choose degrees in the given sector.
- Focus on what the student enjoys doing, wants to learn, or how they like to work.
- Good themes: working with people vs alone, theory vs practice, coding vs design,
  lab work vs writing, health vs business, etc.
- Avoid questions about habits that do not affect degree choice
  (e.g., sleep schedule, generic hobbies, daily routines).

CONTEXT:
- Region: {region}
- Sector: {sector}
- Question #{st.session_state.degree_question_count + 1}
- Previous answers:
{answer_context if answer_context else "None yet."}
{grades_context}
"""

        try:
            question = gemini_client.generate_content(
                prompt="Write the next yes/no question only.",
                system_instruction=system_instruction,
                temperature=0.2,
                user_id=user_id,
                session_id=session_id,
                metadata={"type": "degree_question", "sector": sector, "region": region},
            )
            st.session_state.degree_conversation_history.append(
                {"role": "assistant", "content": question}
            )
            st.rerun()
        except Exception as e:
            st.error(f"⃠ Question error: {e}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ Yes", width='stretch', type="primary"):
            handle_answer("Yes")
    with col2:
        if st.button("⃠ No", width='stretch'):
            handle_answer("No")

    if st.button("↻ Start Over", width='stretch'):
        reset_degree_picker()
        st.rerun()


def handle_answer(answer):
    last_question = st.session_state.degree_conversation_history[-1]["content"]
    st.session_state.degree_answers[last_question] = answer
    st.session_state.degree_conversation_history.append({"role": "user", "content": answer})
    st.session_state.degree_question_count += 1
    st.rerun()


def generate_final_report(gemini_client, sector, user_id, session_id):
    st.markdown("---")
    st.subheader("✉ Your Degree Report")

    if st.session_state.degree_final_report:
        st.markdown(st.session_state.degree_final_report)
        render_save_and_next_controls(sector, st.session_state.degree_final_report)
        return

    with st.spinner("Generating recommendations..."):
        answers_summary = "\n".join(
            [f"Q: {q}\nA: {a}" for q, a in st.session_state.degree_answers.items()]
        )
        grades_context = (
            f"\nGrades: {st.session_state.get('grades_data', 'N/A')}"
            if "grades_data" in st.session_state
            else ""
        )

        region = st.session_state.get("degree_region", "International")

        # portugal validation
        if region == "Portugal":
            report_prompt = f"""You are a DGES specialist creating a degree recommendation for a Portuguese student.

SECTOR: {sector}
STUDENT ANSWERS:
{answers_summary}
{grades_context}

CRITICAL RULES - PORTUGAL ONLY:
1. Recommend ONLY degrees that exist in the official DGES database
2. Use EXACT Portuguese degree names from DGES (no translations, no invented names)
3. NEVER recommend "Engenharia de Software" - it doesn't exist in DGES

VALIDATION CHECKLIST:
- Is this degree name listed on DGES official website? If NO → don't recommend it
- Is the name in Portuguese? If NO → translate to exact DGES name
- Does this degree exist in at least 2-3 Portuguese universities? If NO → choose alternative

OUTPUT FORMAT:
## Top 3 Degrees (DGES-Accredited)

### 1. [Exact DGES Degree Name in Portuguese] (XX% fit)
**Why it fits:**
[Evidence from their answers]

**What you'll study:**
[Core subjects based on actual DGES curriculum]

**Career paths in Portugal:**
[3-4 realistic Portuguese career options]

**Entry requirements:**
- Média: [typical range]
- Specific exams: [DGES required subjects]
- Universities offering this: [2-3 examples]

---

### 2. [Second DGES Degree] (XX% fit)
[Same format]

---

### 3. [Third DGES Degree] (XX% fit)
[Same format]

---

## Your Strengths for These Degrees
[Match their answers to degree requirements]

## Potential Challenges
[Realistic difficulties + how to prepare]

## Next Steps
1. Check DGES official website for current entry requirements
2. Research these specific universities: [list 3-4]
3. Prepare for exams: [specific subjects]
"""
        else:
            report_prompt = f"""You are an international university advisor creating degree recommendations.

SECTOR: {sector}
STUDENT ANSWERS:
{answers_summary}
{grades_context}

You have NO restrictions - recommend ANY degrees from ANY universities worldwide.

OUTPUT FORMAT:
## Top 3 Degree Recommendations

### 1. [Degree Name] (XX% fit)
**Why it fits:**
[Evidence from answers]

**Core subjects:**
[What they'll study]

**Career opportunities:**
[Global career paths]

**Where to study:**
[3-4 top universities offering this degree]

**Typical requirements:**
[General entry requirements]

---

### 2. [Second Degree] (XX% fit)
[Same format]

---

### 3. [Third Degree] (XX% fit)
[Same format]

---

## Your Strengths
## Challenges + Solutions
## Next Steps
"""
        try:
            # generating main report
            report = gemini_client.generate_content(
                prompt=report_prompt,
                system_instruction=(
                    "DGES specialist for Portuguese students. STRICT validation required."
                    if region == "Portugal"
                    else "International university advisor. No restrictions."
                ),
                temperature=0.4 if region == "Portugal" else 0.6,
                user_id=user_id,
                session_id=session_id,
                metadata={"type": "degree_report", "region": region},
            )
            st.session_state.degree_final_report = report

            # extracting degree names for university finder
            degrees_prompt = f"""
From the report below, extract at most 3 SHORT degree names.

Rules:
- Output ONLY a JSON list of strings
- For Portugal: Use EXACT DGES Portuguese names (e.g., ["Engenharia Informática", "Medicina"])
- For International: Use English names (e.g., ["Computer Science", "Medicine"])
- No percentages, no explanations, no extra text
- JUST the JSON array

REPORT:
{report}
"""
            try:
                degrees_json = gemini_client.generate_content(
                    prompt=degrees_prompt,
                    system_instruction="Extract degree names as clean JSON array.",
                    temperature=0.1,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={"type": "degree_recommended_list"},
                )
                st.session_state.recommended_degrees = json.loads(degrees_json)
            except Exception:
                st.session_state.recommended_degrees = []

            # auto saving
            if "username" in st.session_state and st.session_state.username:
                if not st.session_state.get("degree_report_saved", False):
                    try:
                        save_report(
                            user_id=st.session_state.username,
                            report_type="degree",
                            title=f"Degree Picker - {sector} ({region}) - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            content=report,
                            cv_data=None,
                        )
                        st.session_state.degree_report_saved = True
                        st.success("🗂️ Report automatically saved to My Reports!")
                    except Exception as e:
                        st.warning(f"Could not auto-save: {e}")

            st.markdown(report)
            render_save_and_next_controls(sector, report)

        except Exception as e:
            st.error(f"⃠ Report error: {e}")


def render_save_and_next_controls(sector, report):
    st.markdown("---")

    st.download_button(
        "➜] Download Report (TXT)",
        data=report,
        file_name=f"degree_report_{sector.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        width='stretch',
    )

    display_report_footer()


def display_report_footer():
    st.markdown("---")
    st.subheader("What's Next?")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("𖠿 University Finder", width='stretch', key="nav_univ"):
            reset_degree_picker()
            st.session_state.redirect_to = "University Finder"
            st.rerun()

    with col2:
        if st.button("⛶ Grades Analysis", width='stretch', key="nav_grades"):
            reset_degree_picker()
            st.session_state.redirect_to = "Grades Analysis"
            st.rerun()

    with col3:
        if st.button("↺ Career Quiz", width='stretch', key="nav_quiz"):
            reset_degree_picker()
            st.session_state.redirect_to = "Career Quiz"
            st.rerun()

    st.markdown("---")
    if st.button("↻ Retake Degree Picker", width='stretch', key="retake_degree"):
        reset_degree_picker()
        st.rerun()


def reset_degree_picker():
    st.session_state.degree_picker_active = False
    st.session_state.degree_questions = []
    st.session_state.degree_answers = {}
    st.session_state.degree_question_count = 0
    st.session_state.degree_conversation_history = []
    st.session_state.degree_final_report = None
    st.session_state.degree_report_saved = False
