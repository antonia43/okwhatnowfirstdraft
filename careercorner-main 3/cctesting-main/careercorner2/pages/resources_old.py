import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langfuse import observe
from services.langfuse_helper import LangfuseGeminiWrapper
from utils.database import load_reports

load_dotenv()

# raw client for function calling (quick search only)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# wrapper for the chat mode with no function calling
GEMINI_CHAT = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash"
)

def get_job_listings(role: str, location: str = "Portugal") -> dict:
    """Fetching LinkedIn job search links"""
    try:
        params = {
            "keywords": role.replace(' ', '%20'),
            "location": "Portugal",
            "countryCode": "pt",
            "f_TPR": "r86400"
        }
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"https://www.linkedin.com/jobs/search?{query_params}"
        
        return {
            "success": True,
            "count": 50,
            "jobs": [
                {
                    "title": f"{role} (50+ openings)",
                    "company": "Various Companies",
                    "location": "Portugal",
                    "salary": "Competitive",
                    "url": full_url,
                    "description": f"Latest {role} positions in Portugal"
                },
                {
                    "title": f"Senior {role}",
                    "company": "Various Companies",
                    "location": "Portugal",
                    "salary": "€35k-€70k+",
                    "url": full_url.replace("f_TPR=r86400", "f_E=4,5"),
                    "description": "Experienced roles"
                }
            ],
            "message": f"✓ {role} jobs in Portugal"
        }
    except Exception:
        return {
            "success": True,
            "jobs": [{
                "title": f"{role} Jobs",
                "company": "LinkedIn",
                "location": "Portugal",
                "url": f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')}&location=Portugal&countryCode=pt",
                "description": f"Search {role} in Portugal"
            }],
            "message": f"LinkedIn: {role}"
        }


def get_learning_resources(skill: str, career_field: str = "general") -> dict:
    """Top courses"""
    courses_db = {
        "python": [
            {"title": "Python for Everybody", "platform": "Coursera", "url": "https://www.coursera.org/specializations/python", "price": "Free"}
        ],
        "data science": [
            {"title": "IBM Data Science", "platform": "Coursera", "url": "https://www.coursera.org/professional-certificates/ibm-data-science", "price": "Free"}
        ],
        "machine learning": [
            {"title": "Machine Learning", "platform": "Coursera", "url": "https://www.coursera.org/learn/machine-learning", "price": "Free"}
        ],
        "nursing": [
            {"title": "Nursing Essentials", "platform": "Coursera", "url": "https://www.coursera.org/search?query=nursing", "price": "Varies"}
        ]
    }
    
    skill_lower = skill.lower()
    matching_courses = []
    for key, courses in courses_db.items():
        if key in skill_lower or skill_lower in key:
            matching_courses.extend(courses)
    
    if not matching_courses:
        matching_courses = [
            {"title": f"{skill} Courses", "platform": "Coursera", "url": f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}", "price": "Varies"}
        ]
    
    return {"success": True, "skill": skill, "courses": matching_courses[:3], "message": f"✦ {len(matching_courses)} courses"}


# function declarations
JOB_FUNCTION = types.FunctionDeclaration(
    name="get_job_listings",
    description="""Search LinkedIn jobs in Portugal. YOU MUST USE THIS FUNCTION whenever users ask about jobs, work, or career opportunities. Works for ANY company or role.""",
    parameters={
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": "Job role OR company name (e.g., 'Primark', 'nurse', 'Zara cashier')"
            },
            "location": {
                "type": "string",
                "description": "Location in Portugal (default: 'Portugal')"
            }
        },
        "required": ["role"]
    }
)

COURSES_FUNCTION = types.FunctionDeclaration(
    name="get_learning_resources",
    description="Find courses for ANY skill. Always call this when users ask about learning/courses.",
    parameters={
        "type": "object",
        "properties": {
            "skill": {"type": "string", "description": "Skill to learn (e.g., 'art', 'Python')"},
            "career_field": {"type": "string", "description": "Career field (optional)"}
        },
        "required": ["skill"]
    }
)

CAREER_TOOLS = types.Tool(function_declarations=[JOB_FUNCTION, COURSES_FUNCTION])


def execute_career_tool(function_name: str, function_args: dict):
    """Executing tools safely"""
    try:
        if function_name == "get_job_listings":
            return get_job_listings(**function_args)
        elif function_name == "get_learning_resources":
            return get_learning_resources(**function_args)
        return {"error": f"Unknown tool: {function_name}"}
    except Exception as e:
        return {"error": str(e)}


# function calling and observability no wrapper!
@observe(name="professional_resources_quick_search")
def call_gemini_with_tools(prompt: str, user_id: str) -> str:
    """Quick search with function calling"""
    try:
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        
        config = types.GenerateContentConfig(
            tools=[CAREER_TOOLS],
            system_instruction="""You are a career advisor. When users ask about jobs, call get_job_listings(). When users ask about courses, call get_learning_resources().

CRITICAL:
1. ALWAYS call the appropriate function
2. Display ALL links from results with emojis
3. DO NOT ask follow-up questions
4. Be concise and show results immediately"""
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=contents,
            config=config
        )
        
        if response.function_calls:
            function_responses = []
            for fn_call in response.function_calls:
                result = execute_career_tool(fn_call.name, dict(fn_call.args))
                function_responses.append(
                    types.Part.from_function_response(
                        name=fn_call.name,
                        response={"result": result}
                    )
                )
            
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=function_responses))
            
            final_response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=contents,
                config=config
            )
            
            return final_response.text
        
        return response.text
    
    except Exception as e:
        return f"Error: {str(e)}"


def render_main_resources():
    """Quick search with function calling"""
    st.header("𓊍 Career Resources")
    st.info("ⓘ In this section you can quickly find job openings and course suggestions based on what you type, then use the support chat if you want help deciding what to do next!")
    
    
    has_quiz = bool(st.session_state.get("quiz_result"))
    has_cv = bool(st.session_state.get("cv_data"))
    
    if not has_quiz and not has_cv:
        st.info("ⓘ Complete Career Quiz or CV Analysis first")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Career Quiz", width='stretch'):
                st.session_state.redirect_to = "Career Growth"
                st.rerun()
        with col2:
            if st.button("← CV Analysis", width='stretch'):
                st.session_state.redirect_to = "CV Analysis"
                st.rerun()
        return
    
    st.divider()
    st.caption("ⓘ Try: 'data science jobs' or 'Python courses'")
    
    user_query = st.text_input("Quick search:", placeholder="e.g., nursing jobs, art courses")
    
    if st.button("⟡ Search", width='stretch'):
        if user_query:
            with st.spinner("𖦹 Searching..."):
                user_id = st.session_state.get("username", "demo_user")
                
                enhanced_query = f"""User request: {user_query}

INSTRUCTIONS: 
1. Call the appropriate tool (get_job_listings or get_learning_resources)
2. Format results with ALL links provided
3. DO NOT ask follow-up questions
4. Show links clearly with emojis"""
                
                response_text = call_gemini_with_tools(enhanced_query, user_id)
                st.success("☑ Results:")
                st.markdown(response_text)
    
    st.markdown("---")
    if st.button("Need more personalized support?", width='stretch', type="secondary"):
        st.session_state.resources_mode = "chat"
        st.rerun()

def render_resources_chat():
    """Supportive career advisor with no function calling, just chatting"""
    st.header("❤︎ Career Support Chat")

    user_id = st.session_state.get("username", "demo_user")
    
    cv_reports = load_reports(user_id, "professional_cv")
    quiz_reports = load_reports(user_id, "professional_career_quiz")
    
    col1, col2 = st.columns(2)
    with col1:
        if cv_reports:
            cv_options = {f"CV: {r.get('title', 'Untitled')}": r for r in cv_reports}
            selected_cv = st.selectbox(
                "☰ Select CV:", 
                options=list(cv_options.keys()), 
                index=0,
                key="selected_cv"
            )
            selected_cv_data = cv_options[selected_cv]
        else:
            selected_cv_data = None
            st.info("⚠︎ No CV analysis")
    
    with col2:
        if quiz_reports:
            quiz_options = {f"Quiz: {r.get('title', 'Untitled')}": r for r in quiz_reports}
            selected_quiz = st.selectbox(
                "☰ Select Quiz:", 
                options=list(quiz_options.keys()), 
                index=0,
                key="selected_quiz"
            )
            selected_quiz_data = quiz_options[selected_quiz]
        else:
            selected_quiz_data = None
            st.info("⚠︎ No career quiz")
    
    # data summary
    data_summary = f"""Professional Data ({user_id}):
• CVs: {len(cv_reports)} available
• Quizzes: {len(quiz_reports)} available"""
    
    # internal context for the ai
    internal_context = f"""You have access to this professional's data:

SELECTED CV: {selected_cv_data.get('title', 'None') if selected_cv_data else 'None'}
CV Content: {selected_cv_data.get('content', 'No CV uploaded') if selected_cv_data else 'No CV uploaded'}

SELECTED CAREER QUIZ: {selected_quiz_data.get('title', 'None') if selected_quiz_data else 'None'}
Quiz Content: {selected_quiz_data.get('content', 'No quiz completed') if selected_quiz_data else 'No quiz completed'}"""
    
    welcome_message = f"""Hi! I'm here to support you on your career journey!

{data_summary}

I can help you with:  
✦ **Career decisions** based on your CV and quiz results  
✦ **Emotional support** and encouragement  
✦ **Course suggestions** (names/topics - search for links in Quick Search)  
✦ **Next steps** and action planning  

What's on your mind today?"""
    
    if "resources_chat_history" not in st.session_state:
        st.session_state.resources_chat_history = [
            {"role": "assistant", "content": welcome_message}
        ]
    
    for msg in st.session_state.resources_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask for advice, support, or guidance..."):
        st.session_state.resources_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("𖦹 Thinking..."):
                enriched_prompt = f"""{internal_context}

User question: {prompt}

INSTRUCTIONS:
- Be supportive, empathetic, and encouraging
- Reference their CV/quiz data specifically when relevant
- Suggest courses/skills by NAME only (e.g., "Consider learning Python" not links)
- Help them make decisions based on their profile
- If they ask for job/course links, tell them to go back and use the Quick Search feature
- Focus on guidance and support, not direct job searches"""
                
                response_text = GEMINI_CHAT.generate_content(
                    enriched_prompt,
                    user_id=user_id,
                    session_id="pro_support_chat",
                    temperature=0.7
                )
                st.markdown(response_text)
        
        st.session_state.resources_chat_history.append({"role": "assistant", "content": response_text})
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⟲ Restart Chat", width='stretch'):
            st.session_state.resources_chat_history = [
                {"role": "assistant", "content": welcome_message}
            ]
            st.rerun()
    
    with col2:
        if st.button("← Back to Quick Search", width='stretch'):
            if "resources_mode" in st.session_state:
                del st.session_state.resources_mode
            st.rerun()

def render_resources():
    """Toggle Quick Search ↔ Support Chat"""
    if st.session_state.get("resources_mode") == "chat":
        render_resources_chat()
    else:
        render_main_resources()
