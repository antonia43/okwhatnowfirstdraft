# BUILT IN GEMINI GOOGLE TOOLS

import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Raw client for built-in tools
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def get_study_resources_web(subject: str) -> dict:
    """Web search for study resources using Google Search built-in tool"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Find the best free study resources for {subject}. 

Provide DIRECT LINKS to:
- Free online courses (Coursera, edX, Khan Academy, etc.)
- Video tutorials (YouTube channels, playlists)
- Practice websites and tools
- Community resources (Discord, Reddit, forums)
- Study guides and PDFs

Format as a markdown list with clickable links. Include at least 8-10 specific resources with URLs.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        # Extract sources
        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_career_options(course_name: str) -> dict:
    """Get career paths using Google Search"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""What are the top career options and job positions for someone with a degree in {course_name}? 

Provide:
- Entry-level positions with typical titles
- Mid-level career progression
- Senior/leadership roles
- Average salary ranges for each level
- Industry sectors that hire this degree

Use clean markdown formatting with headers and bullet points. Do NOT use code blocks or syntax highlighting.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks[:5]]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_wage_info(job_title: str, country: str = "Portugal") -> dict:
    """Get salary information using Google Search"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""What is the typical salary range for {job_title} in {country}? 

Provide a clear, well-formatted response with:
1. Entry-level salary (annual and monthly)
2. Mid-level salary (annual and monthly)
3. Senior-level salary (annual and monthly)

Use clean markdown with headers and bullet points. Write numbers as plain text (e.g., "$85,000" not in code blocks).""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks[:3]]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_job_search_results(role: str, location: str = "Portugal") -> dict:
    """Job search using Google Search built-in tool"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Find current job opportunities for {role} in {location}.

Provide DIRECT LINKS to:
- Specific job postings (LinkedIn, Indeed, Glassdoor, local job boards)
- Company career pages hiring for this role
- Recruitment agencies specializing in this field
- {location}-specific job platforms

Include at least 10 direct job links with company names and position titles. Format as a markdown list with clickable URLs.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_course_recommendations(skill: str) -> dict:
    """Course search using Google Search"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Find the best online courses to learn {skill}. 

Provide DIRECT LINKS to courses from:
- Coursera
- Udemy
- edX
- Udacity
- LinkedIn Learning
- FreeCodeCamp
- YouTube playlists

Include both free and paid options. Format as markdown with clickable course links.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}



def get_linkedin_profile_optimization(current_headline: str, current_about: str, 
                                      target_role: str, industry: str, skills: str) -> dict:
    """LinkedIn profile optimization using Google Search"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Optimize this LinkedIn profile for a {target_role} in {industry}.

Current Profile:
- Headline: {current_headline}
- About Section: {current_about}
- Skills: {skills}

Provide:
1. 3-5 optimized headline options (keyword-rich, ATS-friendly)
2. Rewritten About section (engaging, professional, with impact statements)
3. Recommended skills to add for this role
4. Profile improvement checklist (photo, banner, featured section ideas)
5. Engagement strategy (posting tips, networking advice)

Research best practices for {target_role} LinkedIn profiles. Use clean markdown formatting. Do NOT use code blocks.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks[:5]]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_company_research(company_name: str) -> dict:
    """Company research using Google Search"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Research {company_name} and provide a comprehensive company profile.

Structure your response exactly like this:

# {company_name}

## Company Overview
[Brief description of company, industry, and size]

## Salary Information
• Average salaries by role level
• Benefits and compensation packages
• Salary comparison to industry average

## Positive Aspects
• Key advantages of working there
• Employee benefits
• Career growth opportunities

## Company Culture
• Work environment and values
• Work-life balance reputation
• Employee sentiment from reviews

## Challenges
• Common concerns from employee reviews
• Potential drawbacks to consider

## Application Tips
• Hiring process overview
• What they look for in candidates
• Interview preparation advice

---

FORMATTING RULES:
- Use standard markdown headers (##)
- Use bullet points (•) for lists
- Write numbers and currency as plain text (not in code blocks)
- NO code formatting or syntax highlighting
- NO escaped characters like \\n
- Be concise and factual""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3  # Lower temperature for more consistent formatting
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks[:8]]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_job_description_from_url(url: str) -> dict:
    """Fetch and extract job description from a URL using Gemini's URL context tool"""
    try:
        # Clean the URL first
        clean_url = url.strip()
        if clean_url.startswith('[') and '](' in clean_url:
            clean_url = clean_url.split('](')[1].rstrip(')')
        clean_url = clean_url.strip('[]() ')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = 'https://' + clean_url
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Analyze this URL and determine if it contains a job posting or job description.
            
            If it IS a job posting:
            - Extract the complete job description including: job title, company, responsibilities, requirements, and any other relevant details.
            - Format as clean text.
            
            If it is NOT a job posting:
            - Return exactly: "NOT_A_JOB_POSTING"
            
            Be strict - only return job content if this is clearly a job listing or career opportunity.""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(url_context=types.UrlContext(url=clean_url))]
            )
        )
        
        # Check if it's not a job posting
        if "NOT_A_JOB_POSTING" in response.text:
            return {
                "success": False,
                "error": "This URL does not appear to contain a job posting. Please provide a link to a job description."
            }

        return {
            "success": True, 
            "job_description": response.text,
            "source_url": clean_url
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e)
        }


def get_city_guide(city_name: str, country: str = "") -> dict:
    """Get comprehensive city guide for students using Google Search"""
    try:
        location = f"{city_name}, {country}" if country else city_name
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Create a comprehensive student guide for {location}.

Structure your response exactly like this:

# {location} Student Guide

## Overview
[2-3 sentences: Brief description of the city, population, and general vibe]

## Universities & Education
[Short intro sentence, then:]
- Major university 1
- Major university 2
- Student population and academic reputation

## Cost of Living
[Short intro sentence, then:]
- Average monthly rent: €XXX-€XXX
- Food and groceries: €XXX/month
- Transportation: €XXX/month
- Overall affordability rating

## Student Life
[Short intro sentence, then:]
- Popular student neighborhoods
- Nightlife and entertainment
- Student discounts and benefits

## Transportation
[Short intro sentence, then:]
- Public transport options (metro, bus, train)
- Student transport passes and prices
- Bike-friendliness

## Culture & Activities
[Short intro sentence, then:]
- Museums, theaters, cultural venues
- Parks and outdoor spaces
- Famous landmarks

## Practical Information
[Short intro sentence, then:]
- Weather and climate
- Safety for students
- Healthcare access
- Language difficulty for internationals

---

**CRITICAL FORMATTING RULES:**
- Use standard markdown headers (##)
- Each section starts with 1 SHORT intro sentence (max 15 words)
- Then use bullet points (•) for details
- Add blank line between sections
- Add blank line between intro sentence and bullets
- Keep bullet points short (1 line each)
- NO code formatting
- NO walls of text
- Break up long paragraphs""",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.4
            )
        )

        sources = []
        metadata = response.candidates[0].grounding_metadata
        if metadata and metadata.grounding_chunks:
            sources = [{"title": c.web.title, "url": c.web.uri} for c in metadata.grounding_chunks[:8]]

        return {"success": True, "answer": response.text, "sources": sources}
    except Exception as e:
        return {"success": False, "error": str(e)}



# Helper function for country selection with "Other" option
def render_country_selector(key_prefix: str, label: str = "Country:", default: str = "Portugal"):
    """Render country dropdown with Other option"""
    countries = [
        "Portugal", "Spain", "United Kingdom", "United States", "Germany", 
        "France", "Italy", "Netherlands", "Canada", "Australia", 
        "Switzerland", "Sweden", "Norway", "Denmark", "Ireland",
        "Belgium", "Austria", "Poland", "Czech Republic", "Japan",
        "Singapore", "UAE", "Brazil", "Other"
    ]

    selected_country = st.selectbox(
        label,
        countries,
        index=countries.index(default) if default in countries else 0,
        key=f"{key_prefix}_country_select"
    )

    if selected_country == "Other":
        custom_country = st.text_input(
            "Enter country name:",
            key=f"{key_prefix}_custom_country",
            placeholder="e.g., South Korea, Mexico, India..."
        )
        if custom_country.strip():
            return custom_country.strip()
        else:
            return "Portugal"  # Default fallback

    return selected_country


# UI Render Functions
def render_city_guide_tool():
    """City guide for students - any city worldwide"""
    st.subheader("City Guide")
    st.info("Discover everything about any city worldwide - perfect for choosing where to study!")

    # Popular university cities worldwide
    popular_cities = {
        "Portugal": ["Lisbon", "Porto", "Coimbra", "Braga", "Aveiro", "Faro"],
        "Spain": ["Barcelona", "Madrid", "Valencia", "Seville", "Granada"],
        "UK": ["London", "Edinburgh", "Manchester", "Oxford", "Cambridge"],
        "USA": ["New York", "Boston", "Los Angeles", "San Francisco", "Chicago"],
        "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Heidelberg"],
        "France": ["Paris", "Lyon", "Toulouse", "Marseille", "Bordeaux"],
        "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Groningen"],
        "Italy": ["Rome", "Milan", "Florence", "Bologna", "Turin"],
        "Other": ["Other"]
    }

    col1, col2 = st.columns(2)
    
    with col1:
        country = st.selectbox(
            "Select country:",
            list(popular_cities.keys()),
            key="city_guide_country"
        )
    
    with col2:
        if country != "Other":
            city = st.selectbox(
                "Select city:",
                popular_cities[country] + ["Other"],
                key="city_guide_city"
            )
        else:
            # If "Other" country selected, skip city dropdown entirely
            city = "Other"

    # Show text inputs when "Other" is selected
    if city == "Other" or country == "Other":
        col1, col2 = st.columns(2)
        with col1:
            custom_city = st.text_input(
                "City name:",
                placeholder="e.g., Tokyo, Singapore, Toronto...",
                key="city_guide_custom_city"
            )
        with col2:
            custom_country = st.text_input(
                "Country:",
                placeholder="e.g., Japan, Singapore, Canada..." if country == "Other" else country,
                value="" if country == "Other" else country,
                key="city_guide_custom_country",
                disabled=(country != "Other")  # Disable if country already selected
            )
        
        final_city = custom_city.strip()
        final_country = custom_country.strip() if country == "Other" else country
    else:
        final_city = city
        final_country = country

    # Disable button if required fields are empty
    can_search = bool(final_city and final_city != "Other" and final_country and final_country != "Other")

    if st.button("Explore City", width="stretch", type="primary", disabled=not can_search):
        with st.spinner(f"Researching {final_city}..."):
            results = get_city_guide(final_city, final_country)
            if results["success"]:
                st.markdown(results["answer"])

                if results["sources"]:
                    with st.expander("View Sources"):
                        for source in results["sources"]:
                            st.markdown(f"[{source['title']}]({source['url']})")
            else:
                st.error(f"Error: {results.get('error', 'Unknown error')}")
    
    if not can_search and (city == "Other" or country == "Other"):
        st.caption("ⓘ Tip: Enter a city name to search")
    else:
        st.caption("ⓘ Tip: Compare multiple cities to find the perfect match for your study abroad plans!")


def render_exam_papers_tool():
    """IAVE exam papers - direct links only"""
    st.subheader("Past Exam Papers")
    st.info("Access official IAVE nacional exam papers from previous years")


    st.markdown("### Current Year Exams")
    st.caption("Browse the latest nacional exams")
    st.link_button(
        "Open IAVE Current Exams",
        "https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/",
        width="stretch",
        type="primary"
    )


    st.markdown("### Complete Archive (All Years)")
    st.caption("Access past papers from all previous years")
    st.link_button(
        "Open IAVE Archive",
        "https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/",
        width="stretch",
        type="primary"
    )

    st.caption("✪ Tip: Practice with past papers to improve your exam technique!")


def render_scholarships_tool():
    """Scholarship links"""
    st.subheader("Scholarships & Financial Aid")
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
                f"Visit {scholarship['name']}",
                scholarship['url'],
                width="stretch"
            )
            st.divider()


def render_study_resources_tool():
    """Study resources with Google Search"""
    st.subheader("Study Resources")
    st.info("Find direct links to learning materials for any subject")

    subject = st.text_input(
        "What subject do you want to study?",
        placeholder="e.g., Python, Biology, Calculus, History...",
        key="study_resources_subject"
    )

    if st.button("Search Study Resources", width="stretch", type="primary"):
        if subject.strip():
            with st.spinner(f"Finding resources for {subject}..."):
                results = get_study_resources_web(subject.strip())
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a subject")


def render_career_options_tool():
    """Career options using Google Search"""
    st.subheader("Career Options Explorer")
    st.info("Discover what careers you can pursue with your degree")

    course = st.text_input(
        "What degree/course are you interested in?",
        placeholder="e.g., Computer Science, Medicine, Psychology...",
        key="career_options_course"
    )

    if st.button("Explore Career Options", width="stretch", type="primary"):
        if course.strip():
            with st.spinner(f"Finding careers for {course}..."):
                results = get_career_options(course.strip())
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a course name")



def render_wage_finder_tool():
    """Salary information using Google Search"""
    st.subheader("Wage Finder")
    st.info("Find salary ranges for different job positions")

    col1, col2 = st.columns([2, 1])

    with col1:
        job_title = st.text_input(
            "Job title:",
            placeholder="e.g., Software Engineer, Nurse, Teacher...",
            key="wage_finder_job"
        )

    with col2:
        country = render_country_selector("wage_finder", "Country:", "Portugal")

    if st.button("Search Salaries", width="stretch", type="primary"):
        if job_title.strip():
            with st.spinner(f"Finding salary data for {job_title}..."):
                results = get_wage_info(job_title.strip(), country)
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a job title")


def render_job_search_tool():
    """Job search with Google Search"""
    st.subheader("Job Search")
    st.info("Find direct links to job opportunities in your field")

    col1, col2 = st.columns([2, 1])

    with col1:
        role = st.text_input(
            "Job role or company:",
            placeholder="e.g., Software Engineer, Marketing Manager...",
            key="job_search_role"
        )

    with col2:
        # Custom location selector for job search (cities + countries)
        locations = [
            "Portugal", "Lisbon", "Porto", "Spain", "Barcelona", "Madrid",
            "United Kingdom", "London", "Germany", "Berlin", "Netherlands", 
            "Amsterdam", "Remote", "United States", "Canada", "France", 
            "Italy", "Switzerland", "Other"
        ]

        location = st.selectbox(
            "Location:",
            locations,
            key="job_search_location"
        )

        if location == "Other":
            custom_location = st.text_input(
                "Enter location:",
                key="job_search_custom_location",
                placeholder="e.g., Singapore, Dubai, Tokyo..."
            )
            if custom_location.strip():
                location = custom_location.strip()
            else:
                location = "Portugal"

    if st.button("Search Jobs", width="stretch", type="primary"):
        if role.strip():
            with st.spinner(f"Searching for {role} jobs in {location}..."):
                results = get_job_search_results(role.strip(), location)
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a job role")


def render_course_finder_tool():
    """Course finder with Google Search"""
    st.subheader("Course Finder")
    st.info("Discover direct links to courses for learning new skills")

    skill = st.text_input(
        "What skill do you want to learn?",
        placeholder="e.g., Python, Data Analysis, Project Management...",
        key="course_finder_skill"
    )

    if st.button("Find Courses", width="stretch", type="primary"):
        if skill.strip():
            with st.spinner(f"Finding courses for {skill}..."):
                results = get_course_recommendations(skill.strip())
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a skill to learn")
            

def render_linkedin_optimizer_tool():
    """LinkedIn profile optimization using Google Search"""
    st.subheader("LinkedIn Profile Optimizer")
    st.info("Get AI-powered suggestions to optimize your LinkedIn profile for recruiters")

    st.markdown("### Current Profile Information")

    current_headline = st.text_input(
        "Current Headline:",
        placeholder="e.g., Student at University of Lisbon",
        key="linkedin_current_headline"
    )

    current_about = st.text_area(
        "Current About Section:",
        placeholder="Paste your current About/Summary section here...",
        height=150,
        key="linkedin_current_about"
    )

    st.markdown("### Target Information")

    col1, col2 = st.columns(2)

    with col1:
        target_role = st.text_input(
            "Target Job Role:",
            placeholder="e.g., Data Scientist, Software Engineer",
            key="linkedin_target_role"
        )

    with col2:
        industry = st.selectbox(
            "Industry:",
            ["Technology", "Healthcare", "Finance", "Marketing", "Education", 
             "Engineering", "Consulting", "Sales", "Design", "Other"],
            key="linkedin_industry"
        )

    skills = st.text_input(
        "Your Current Skills (comma-separated):",
        placeholder="e.g., Python, Machine Learning, Data Analysis",
        key="linkedin_skills"
    )

    if st.button("Optimize My Profile", width="stretch", type="primary"):
        if current_headline.strip() and target_role.strip():
            with st.spinner("Analyzing your profile and researching best practices..."):
                results = get_linkedin_profile_optimization(
                    current_headline.strip(),
                    current_about.strip() if current_about.strip() else "No about section provided",
                    target_role.strip(),
                    industry,
                    skills.strip() if skills.strip() else "No skills provided"
                )
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please provide at least your current headline and target role")


def render_company_research_tool():
    """Company research using Google Search"""
    st.subheader("Company Research")
    st.info("Research companies before you apply - learn about culture, reviews, salary and more")

    company_name = st.text_input(
        "Company name:",
        placeholder="e.g., Google, Microsoft, Deloitte, Zara...",
        key="company_research_name"
    )

    if st.button("Research Company", width="stretch", type="primary"):
        if company_name.strip():
            with st.spinner(f"Researching {company_name}..."):
                results = get_company_research(company_name.strip())
                if results["success"]:
                    st.markdown(results["answer"])

                    if results["sources"]:
                        with st.expander("View Sources"):
                            for source in results["sources"]:
                                st.markdown(f"[{source['title']}]({source['url']})")
                else:
                    st.error(f"Error: {results.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a company name")
