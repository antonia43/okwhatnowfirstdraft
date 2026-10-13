import streamlit as st
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
from utils.database import save_report
from datetime import datetime
import os
import re
from dotenv import load_dotenv

load_dotenv()

QUIZ_GEMINI = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)


def render_student_career_quiz():
    st.header("★ Career Discovery Quiz")

    # initialising state
    if "career_quiz_active" not in st.session_state:
        st.session_state.career_quiz_active = False
    if "career_quiz_answers" not in st.session_state:
        st.session_state.career_quiz_answers = []
    if "career_quiz_question_num" not in st.session_state:
        st.session_state.career_quiz_question_num = 0
    if "career_quiz_current_question" not in st.session_state:
        st.session_state.career_quiz_current_question = None
    if "career_quiz_final_report" not in st.session_state:
        st.session_state.career_quiz_final_report = None
    if "career_quiz_saved" not in st.session_state:
        st.session_state.career_quiz_saved = False

    if not st.session_state.career_quiz_active:
        render_quiz_intro()
    elif st.session_state.career_quiz_final_report:
        render_final_report()
    else:
        render_quiz_questions()


def render_quiz_intro():
    st.markdown("""
    ### Discover Your Career Path

    This isn't your typical career quiz. We'll ask you some **creative questions** that reveal:  
    ✦ How you think and solve problems  
    ✦ What you value and enjoy  
    ✦ Your natural strengths (even ones you don't realize!)  

    **No wrong answers.** Just be honest and spontaneous.  

    **What you'll get:**  
    ✦ Your top 3 career sectors with fit percentages  
    ✦ Hidden skills you didn't know you had  
    ✦ Personalized career paths you've never considered  
    """)

    st.markdown("---")

    if st.button("⟡ Start Discovery Quiz", width='stretch', type="primary"):
        st.session_state.career_quiz_active = True
        st.session_state.career_quiz_question_num = 0
        st.session_state.career_quiz_answers = []
        st.rerun()


def render_quiz_questions():
    MAX_QUESTIONS = 10
    current_q_num = st.session_state.career_quiz_question_num

    # checking if done
    if current_q_num >= MAX_QUESTIONS:
        generate_final_report()
        st.rerun()
        return

    # progress
    st.progress((current_q_num + 1) / MAX_QUESTIONS)
    st.caption(f"Question {current_q_num + 1} of {MAX_QUESTIONS}")
    st.markdown("---")

    # generating question if needed
    if st.session_state.career_quiz_current_question is None:
        generate_next_question()
        st.rerun()
        return

    # displaying the question
    question = st.session_state.career_quiz_current_question
    st.subheader(question)

    # text input for answer
    answer = st.text_area(
        "Your answer:",
        height=150,
        placeholder="Take your time... there's no right or wrong answer.",
        key=f"answer_{current_q_num}"
    )

    st.markdown("---")

    col1, col2 = st.columns([1, 4])

    with col1:
        if current_q_num > 0:
            if st.button("← Back", width='stretch'):
                st.session_state.career_quiz_question_num -= 1
                st.session_state.career_quiz_current_question = None
                # removing last answer
                if st.session_state.career_quiz_answers:
                    st.session_state.career_quiz_answers.pop()
                st.rerun()

    with col2:
        if st.button("Next →", width='stretch', type="primary"):
            if answer.strip():
                # saving answer
                st.session_state.career_quiz_answers.append({
                    "question": question,
                    "answer": answer.strip(),
                    "question_number": current_q_num + 1
                })
                st.session_state.career_quiz_question_num += 1
                st.session_state.career_quiz_current_question = None
                st.rerun()
            else:
                st.warning("Please write an answer before continuing!")

def generate_next_question():
    """Generating adaptive question based on previous answers"""
    q_num = st.session_state.career_quiz_question_num
    previous_answers = st.session_state.career_quiz_answers

    # building context from previous answers
    context = ""
    if previous_answers:
        context = "Previous answers:\n" + "\n".join([
            f"Q{a['question_number']}: {a['question']}\nA: {a['answer'][:100]}..."
            for a in previous_answers[-3:]
        ])

    prompt = f"""You are a creative career counselor designing a fun, engaging personality quiz.

Current question number: {q_num + 1} of 10

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
        question = QUIZ_GEMINI.generate_content(
            prompt=prompt,
            system_instruction="Return ONLY one fun, concrete question under 15 words. NO abstract philosophy. NO career references. Make it relatable and easy to answer.",
            temperature=0.8,  # Reduced from 0.9 for more consistency
            user_id=get_user_id(),
            session_id=get_session_id(),
            metadata={"type": "adaptive_career_question", "q_num": q_num}
        )

        st.session_state.career_quiz_current_question = question.strip()

    except Exception as e:
        st.error(f"Error generating question: {e}")
        # Updated fallback questions - more fun and concrete
        fallback_questions = [
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
        st.session_state.career_quiz_current_question = fallback_questions[q_num % len(fallback_questions)]


def generate_final_report():
    """Analysing all answers and generate comprehensive career report"""

    answers = st.session_state.career_quiz_answers
    # building full conversation history
    qa_text = "\n\n".join([
        f"Q{a['question_number']}: {a['question']}\nAnswer: {a['answer']}"
        for a in answers
    ])

    prompt = f"""You are an expert career psychologist analyzing quiz responses to find the BEST career sectors for this student.

QUIZ RESPONSES:
{qa_text}

ANALYSIS TASK:
1. Identify TOP 1-3 BROAD SECTORS with fit percentages (must add to 100%)
2. Within each sector, find 2-3 SPECIFIC CAREER PATHS
3. Reveal hidden skills with evidence from answers

BROAD SECTORS TO CHOOSE FROM:
Technology, Healthcare, Business, Engineering, Creative Arts, Education, Science, Law, Social Services, Media & Communications, Hospitality, Sports & Fitness, Environment, Public Service

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

1. Explore degrees in [Primary Sector] using the Degree Picker
2. Research careers: [3 specific job titles]
3. Develop: [2 skills to enhance fit]

## Your Profile Summary
[2-3 sentences describing unique approach/style/values]

---
*Report generated {datetime.now().strftime('%Y-%m-%d')}*
"""

    try:
        with st.spinner("Analyzing your responses and discovering your perfect career match..."):
            report = QUIZ_GEMINI.generate_content(
                prompt=prompt,
                system_instruction="You are an expert career psychologist. Give broad sectors with % AND specific paths within them.",
                temperature=0.6,
                user_id=get_user_id(),
                session_id=get_session_id(),
                metadata={"type": "career_discovery_report"}
            )

            st.session_state.career_quiz_final_report = report

            # FIXED: Pattern matches "### 1. Creative Arts (50%)" format
            sector_pattern = r'###\s*\d+\.\s*([A-Za-z\s&]+)\s*\((\d+)%\)'
            sector_matches = re.findall(sector_pattern, report)

            if sector_matches:
                # storing sectors with percentages (strip whitespace from sector names)
                sectors_dict = {sector.strip(): int(pct) for sector, pct in sector_matches}

                # primary = highest %
                primary_sector = max(sectors_dict.items(), key=lambda x: x[1])[0]

                # saving for dropdowns
                st.session_state.recommended_sectors = sectors_dict  # {'Healthcare': 60, 'Education': 40}
                st.session_state.recommended_sector = primary_sector  # 'Healthcare'

                # also saving as formatted string for display
                st.session_state.sectors_display = ", ".join([f"{s} ({p}%)" for s, p in sectors_dict.items()])

                # Debug logging
                print(f"✓ Extracted sectors: {sectors_dict}")
                print(f"✓ Primary sector: {primary_sector}")
            else:
                # fallback
                print("⚠ No sectors matched regex pattern, using fallback")
                st.session_state.recommended_sector = "General"
                st.session_state.recommended_sectors = {"General": 100}
                st.session_state.sectors_display = "General (100%)"

    except Exception as e:
        st.error(f"⚠︎ Error generating report: {e}")
        st.session_state.career_quiz_final_report = "Error generating report. Please try again."


def render_final_report():
    st.markdown("---")
    # st.header("Your Career Discovery Results")

    report = st.session_state.career_quiz_final_report
    st.markdown(report)

    # auto saving to our database
    if "username" in st.session_state and st.session_state.username:
        if not st.session_state.career_quiz_saved:
            try:
                sector = st.session_state.get("recommended_sector", "Career Discovery")

                save_report(
                    user_id=st.session_state.username,
                    report_type="career_quiz",
                    title=f"Career Quiz - {sector} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content=report,
                    cv_data={
                        "recommended_sector": st.session_state.get("recommended_sector"),  # FIXED
                        "recommended_sectors": st.session_state.get("recommended_sectors"),  # FIXED
                        "sectors_display": st.session_state.get("sectors_display"),
                    },
                )

                st.session_state.career_quiz_saved = True
                st.success("🗂️ Results automatically saved to My Reports!")

            except Exception as e:
                st.warning(f"Could not auto-save: {e}")

    # download button
    st.markdown("---")
    st.download_button(
        "➜] Download Report (TXT)",
        data=report,
        file_name=f"career_discovery_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        width='stretch'
    )

    st.markdown("---")
    st.subheader("What's Next?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("𖦏 Find Degrees", width='stretch', key="quiz_to_degree"):
            reset_quiz()
            st.session_state.redirect_to = "Degree Picker"
            st.rerun()

    with col2:
        if st.button("𖠿 Find Universities", width='stretch', key="quiz_to_uni"):
            reset_quiz()
            st.session_state.redirect_to = "University Finder"
            st.rerun()

    with col3:
        if st.button("⛶ Analyze Grades", width='stretch', key="quiz_to_grades"):
            reset_quiz()
            st.session_state.redirect_to = "Grades Analysis"
            st.rerun()

    st.markdown("---")

    if st.button("↻ Retake Quiz", width='stretch'):
        reset_quiz()
        st.rerun()



def reset_quiz():
    st.session_state.career_quiz_active = False
    st.session_state.career_quiz_answers = []
    st.session_state.career_quiz_question_num = 0
    st.session_state.career_quiz_current_question = None
    st.session_state.career_quiz_final_report = None
    st.session_state.career_quiz_saved = False
