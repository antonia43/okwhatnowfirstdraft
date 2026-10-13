import streamlit as st
import os
from dotenv import load_dotenv
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id

load_dotenv()

# Gemini 2.5 Flash for all tools
GEMINI = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash"
)

def get_study_resources_web(subject: str) -> str:
    """Web search for study resources on any subject"""
    prompt = f"""Find the best study resources for: {subject}

Return a formatted list with:
- Free online courses (Coursera, edX, Khan Academy)
- Video tutorials (YouTube channels, video series)
- Practice materials (exercises, quizzes, worksheets)
- Community resources (Reddit, Discord, study groups)

Format each resource as:
**Resource Name** - Brief description
Link: [URL if known]

Be specific and helpful. Focus on FREE resources."""

    response = GEMINI.generate_content(
        prompt=prompt,
        user_id=get_user_id(),
        session_id=get_session_id(),
        temperature=0.3,
        metadata={"type": "study_resources", "subject": subject}
    )
    
    return response if response else "Could not find study resources."


def get_career_options(course_name: str) -> str:
    """Get potential career paths for a degree/course"""
    prompt = f"""List potential career options for someone with a degree in: {course_name}

Provide:
1. **Common Career Paths** (5-7 realistic job titles)
2. **Emerging Opportunities** (3-4 newer/growing roles)
3. **Industry Sectors** (where these professionals work)
4. **Key Skills Needed** (top 5 skills employers want)

Format clearly with emojis. Be specific about Portuguese market if relevant, but include international opportunities too."""

    response = GEMINI.generate_content(
        prompt=prompt,
        user_id=get_user_id(),
        session_id=get_session_id(),
        temperature=0.4,
        metadata={"type": "career_options", "course": course_name}
    )
    
    return response if response else "Could not find career information."


def get_wage_info(job_title: str, country: str = "Portugal") -> str:
    """Get salary information for a job title"""
    prompt = f"""Provide salary information for: {job_title} in {country}

Include:
1. **Entry-Level Salary** (0-2 years experience)
2. **Mid-Level Salary** (3-7 years experience)
3. **Senior-Level Salary** (8+ years experience)
4. **Factors Affecting Salary** (location, company size, industry)
5. **Salary Trends** (growing/stable/declining)

Use:
- € for Portugal/Europe
- Provide monthly AND annual figures
- Be realistic and cite sources if possible (e.g., "According to Glassdoor...")
- Mention if data is limited

Format clearly with salary ranges."""

    response = GEMINI.generate_content(
        prompt=prompt,
        user_id=get_user_id(),
        session_id=get_session_id(),
        temperature=0.2,
        metadata={"type": "wage_info", "job": job_title, "country": country}
    )
    
    return response if response else "Could not find wage information."


def render_exam_papers_tool():
    """IAVE exam papers - direct links only"""
    st.subheader("✍︎ Past Exam Papers")
    st.info("ⓘ Access official IAVE nacional exam papers from previous years")
    
    st.markdown("---")
    
    # Current year exams
    st.markdown("###✍︎ Current Year Exams")
    st.caption("Browse the latest nacional exams")
    st.link_button(
        "Open IAVE Current Exams",
        "https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/",
        use_container_width=True,
        type="primary"
    )
    
    st.markdown("---")
    
    # Complete archive
    st.markdown("### Complete Archive (All Years)")
    st.caption("Access past papers from all previous years")
    st.link_button(
        "Open IAVE Archive",
        "https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/",
        use_container_width=True,
        type="primary"
    )
    
    st.markdown("---")
    st.caption("ⓘ Tip: Practice with past papers to improve your exam technique!")

def render_scholarships_tool():
    """Scholarship links"""
    st.subheader("✪ Scholarships Finder")
    st.info("Find scholarships from DGES, FCT, Erasmus+, and more")
    
    scholarships = [
        {
            "name": "DGES Scholarships",
            "description": "Portuguese government scholarships for higher education",
            "url": "https://www.dges.gov.pt/pt/pagina/bolsas-de-estudo"
        },
        {
            "name": "FCT Research Grants",
            "description": "Funding for research and postgraduate studies",
            "url": "https://www.fct.pt/apoios/bolsas/"
        },
        {
            "name": "Erasmus+ Mobility",
            "description": "Study abroad opportunities in Europe",
            "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students"
        }
    ]
    
    for scholarship in scholarships:
        with st.container():
            st.markdown(f"**{scholarship['name']}**")
            st.caption(scholarship['description'])
            st.link_button(
                f" Visit {scholarship['name']}",
                scholarship['url'],
                use_container_width=True
            )
            st.divider()


def render_study_resources_tool():
    """Study resources with web search"""
    st.subheader("✎ Study Resources")
    st.info("Find the best learning materials for any subject")
    
    subject = st.text_input(
        "What subject do you want to study?",
        placeholder="e.g., Python, Biology, Calculus, History...",
        key="study_resources_subject"
    )
    
    if st.button("🔍 Search Study Resources", use_container_width=True, type="primary"):
        if subject.strip():
            with st.spinner(f"Finding resources for {subject}..."):
                results = get_study_resources_web(subject.strip())
                st.success("✓ Found resources!")
                st.markdown(results)
        else:
            st.warning("Please enter a subject")


def render_career_options_tool():
    """Career options for a course"""
    st.subheader(" Career Options Explorer")
    st.info("Discover what careers you can pursue with your degree")
    
    course = st.text_input(
        "What degree/course are you interested in?",
        placeholder="e.g., Computer Science, Medicine, Psychology...",
        key="career_options_course"
    )
    
    if st.button("Explore Career Options", use_container_width=True, type="primary"):
        if course.strip():
            with st.spinner(f"Finding careers for {course}..."):
                results = get_career_options(course.strip())
                st.success("✓ Career paths found!")
                st.markdown(results)
        else:
            st.warning("Please enter a course name")


def render_wage_finder_tool():
    """Salary information finder"""
    st.subheader("$ Wage Finder")
    st.info("Find salary ranges for different job positions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_title = st.text_input(
            "Job title:",
            placeholder="e.g., Software Engineer, Nurse, Teacher...",
            key="wage_finder_job"
        )
    
    with col2:
        country = st.selectbox(
            "Country:",
            ["Portugal", "Spain", "UK", "USA", "Germany", "France", "Other"],
            key="wage_finder_country"
        )
    
    if st.button("Search Salaries", use_container_width=True, type="primary"):
        if job_title.strip():
            with st.spinner(f"Finding salary data for {job_title}..."):
                results = get_wage_info(job_title.strip(), country)
                st.success("✓ Salary information found!")
                st.markdown(results)
        else:
            st.warning("Please enter a job title")
