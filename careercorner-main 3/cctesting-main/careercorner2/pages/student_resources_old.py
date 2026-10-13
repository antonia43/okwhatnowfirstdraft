import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langfuse import observe
from services.langfuse_helper import LangfuseGeminiWrapper
from utils.database import get_saved_universities, load_reports

load_dotenv()

# raw client for function calling for quick search only
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# wrapper for chat mode (no function calling)
GEMINI_CHAT = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash"
)

def get_study_resources(subject: str) -> dict:
    """Dynamic study resources for any subject"""
    subject_encoded = subject.replace(' ', '%20')
    subject_plus = subject.replace(' ', '+')
    
    return {
        "success": True,
        "subject": subject,
        "resources": [
            {
                "title": f"{subject} on Khan Academy",
                "url": f"https://www.khanacademy.org/search?search_again=1&page_search_query={subject_plus}",
                "type": "Videos & Practice",
                "description": "K-12 to university level"
            },
            {
                "title": f"{subject} Courses on Coursera",
                "url": f"https://www.coursera.org/search?query={subject_encoded}",
                "type": "University Courses",
                "description": "Free and paid courses"
            },
            {
                "title": f"{subject} on YouTube",
                "url": f"https://www.youtube.com/results?search_query={subject_plus}+tutorial",
                "type": "Video Tutorials",
                "description": "Free tutorials and lectures"
            },
            {
                "title": f"{subject} Study Sets on Quizlet",
                "url": f"https://quizlet.com/subject/{subject.replace(' ', '-').lower()}",
                "type": "Flashcards & Quizzes",
                "description": "Community study materials"
            },
            {
                "title": f"{subject} on Reddit",
                "url": f"https://www.reddit.com/search/?q={subject_plus}+study+resources",
                "type": "Community",
                "description": "Study tips and resources from students"
            }
        ],
        "message": f"Top {subject} study resources"
    }

def get_portugal_scholarships(degree: str = "") -> dict:
    """DGES/FCT/Erasmus scholarships"""
    return {
        "success": True,
        "scholarships": [
            {"name": "DGES Bolsas", "url": "https://www.dges.gov.pt/pt/pagina/bolsas-de-estudo"},
            {"name": "FCT Bolsas", "url": "https://www.fct.pt/apoios/bolsas/"},
            {"name": "Erasmus+ Scholarships", "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students"}
        ],
        "message": "Scholarships in Portugal"
    }
    
def get_exam_past_papers(subject: str = "") -> dict:
    """IAVE nacional exams past papers"""
    return {
        "success": True,
        "papers": [
            {
                "year": "Current Year Exams", 
                "url": "https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/",
                "description": "Browse latest nacional exams"
            },
            {
                "year": "All Past Papers Archive", 
                "url": "https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/",
                "description": "Complete archive (all subjects)"
            }
        ],
        "message": "IAVE Exam Papers:"
    }


def get_cif_improvement_tips(cif_score: float) -> dict:
    """Improving CIF +2 points with personalized advice"""
    target = cif_score + 2
    
    if cif_score < 14.0:
        tips = [
            f"CIF {cif_score} → Target {target}",
            "⟡ Priority: Master exam technique (35% weight = biggest impact)",
            "⟡ Focus on your 3 strongest subjects first (build confidence)",
            "⟡ Study plan: 2 hours/day minimum (consistent > intense)",
            "⟡ Practice 10+ past papers per subject (IAVE/DGES archives)",
            "⟡ Target: +1.5 points from exams, +0.5 from school average"
        ]
    elif 14.0 <= cif_score < 16.0:
        tips = [
            f"CIF {cif_score} → Target {target}",
            "⟡ Priority: Balance school grades + exam prep (both matter)",
            "⟡ National exams: Daily practice (35% weight, easiest to improve)",
            "⟡ School grades: Focus on weakest subject (+1 point = +0.65 CIF)",
            "⟡ Study groups: Collaborate for difficult topics",
            "⟡ Target: +1.2 from exams, +0.8 from school improvement"
        ]
    elif 16.0 <= cif_score < 18.0:
        tips = [
            f"CIF {cif_score} → Target {target}",
            "⟡ Priority: Perfect exam execution (you're close to top tier)",
            "⟡ Time management: Practice full exams under timed conditions",
            "⟡ Analyze mistakes: Review every wrong answer (find patterns)",
            "⟡ Target perfection in strongest subject (aim for 19-20)",
            "⟡ Target: +1.0 from exam optimization, +1.0 from consistency"
        ]
    else:
        tips = [
            f"CIF {cif_score} → Target {target} (top 5% territory!)",
            "⟡ Priority: Maintain excellence + reduce exam anxiety",
            "⟡ Mental prep: Mock exams for confidence (not knowledge gaps)",
            "⟡ Double-check: Avoid careless mistakes (biggest risk at this level)",
            "⟡ Stretch goal: Perfect score in one exam (psychological boost)",
            "⟡ You're already competitive for top universities!"
        ]
    
    tips.append("ⓘ Past papers: https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/")
    
    return {
        "success": True,
        "current_cif": cif_score,
        "target_cif": target,
        "tips": tips,
        "message": f"+2 CIF points achievable"
    }


# function declarations
STUDY_FUNCTION = types.FunctionDeclaration(
    name="get_study_resources",
    description="Get study resources from Khan Academy, Coursera, YouTube, Quizlet, Reddit. Works for ANY subject.",
    parameters={
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Subject to study (e.g., 'Python', 'biology', 'math')"}
        },
        "required": ["subject"]
    }
)

SCHOLARSHIP_FUNCTION = types.FunctionDeclaration(
    name="get_portugal_scholarships",
    description="Find scholarships from DGES, FCT, Erasmus, Nova Merit, Santander",
    parameters={
        "type": "object",
        "properties": {
            "degree": {"type": "string", "description": "Degree field (e.g., 'computer science', 'engineering')"}
        },
        "required": ["degree"]
    }
)

EXAM_FUNCTION = types.FunctionDeclaration(
    name="get_exam_past_papers",
    description="Get DGES/IAVE nacional exam past papers (2024-2025)",
    parameters={
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Exam subject (e.g., 'Math', 'Physics')"}
        },
        "required": ["subject"]
    }
)

CIF_FUNCTION = types.FunctionDeclaration(
    name="get_cif_improvement_tips",
    description="Get personalized tips to improve CIF score by +2 points",
    parameters={
        "type": "object",
        "properties": {
            "cif_score": {"type": "number", "description": "Current CIF score (0-20 scale)"}
        },
        "required": ["cif_score"]
    }
)


STUDENT_TOOLS = types.Tool(function_declarations=[
    STUDY_FUNCTION, SCHOLARSHIP_FUNCTION, EXAM_FUNCTION, CIF_FUNCTION
])


def execute_student_tool(function_name: str, function_args: dict):
    """Executing student tools safely"""
    try:
        if function_name == "get_study_resources":
            return get_study_resources(**function_args)
        elif function_name == "get_portugal_scholarships":
            return get_portugal_scholarships(**function_args)
        elif function_name == "get_exam_past_papers":
            return get_exam_past_papers(**function_args)
        elif function_name == "get_cif_improvement_tips":
            return get_cif_improvement_tips(**function_args)
        return {"error": f"Unknown tool: {function_name}"}
    except Exception as e:
        return {"error": str(e)}


# function calling for quick search with observability (no wrappper)
@observe(name="student_resources_quick_search")
def call_gemini_with_student_tools(prompt: str, user_id: str) -> str:
    """Quick search with function calling"""
    try:
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        
        config = types.GenerateContentConfig(
            tools=[STUDENT_TOOLS],
            system_instruction="""You are a student academic advisor in Portugal.

When users ask about study resources, scholarships, exams or CIF tips:
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
                result = execute_student_tool(fn_call.name, dict(fn_call.args))
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

def render_student_main_resources():
    """Quick student tools with function calling"""
    st.header("✄ Student Resources")
    st.info("ⓘ Quick search or personalized support chat")

    user_id = st.session_state.get("username", "demo_user")
    
    try:
        degree_reports = load_reports(user_id, "degree")
        grades_reports = load_reports(user_id, "grades")
        saved_unis = get_saved_universities(user_id)
        
        has_degree = len(degree_reports) > 0
        has_grades = len(grades_reports) > 0
        has_unis = len(saved_unis) > 0
        
        if has_degree or has_grades or has_unis:
            st.success(f"✓ Loaded {len(degree_reports)} degrees, {len(grades_reports)} grades, {len(saved_unis)} unis")
        else:
            st.info("💡 Tip: For better personalized advice, try Degree Picker or Grades Analysis first!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Degree Picker", key="degree_picker_btn", width='stretch'):
                    st.session_state.redirect_to = "Degree Picker"
                    st.rerun()
            with col2:
                if st.button("← Grades Analysis", key="grades_analysis_btn", width='stretch'):
                    st.session_state.redirect_to = "Grades Analysis"
                    st.rerun()
            # Removed return - let them continue even without data
    except:
        pass
    
    
    st.divider()
    st.caption("ⓘ Try: 'biology resources', 'engineering scholarships', 'CIF 15.2 tips'")
    
    user_query = st.text_input("Quick search:", placeholder="e.g., math study resources", key="student_quick_search")
    
    if st.button("⟡ Search", key="student_search_btn", width='stretch'):
        if user_query:
            with st.spinner("Searching..."):
                enhanced_query = f"""User request: {user_query}

INSTRUCTIONS: 
1. Call the appropriate tool
2. Format results with ALL links
3. DO NOT ask follow-up questions
4. Show links clearly with emojis"""
                
                response_text = call_gemini_with_student_tools(enhanced_query, user_id)
                st.success("☑ Results:")
                st.markdown(response_text)
    
    st.markdown("---")
    if st.button("Need more personalized support?", key="student_chat_mode_btn", width='stretch', type="secondary"):
        st.session_state.resources_mode = "chat"
        st.rerun()


def render_student_resources_chat():
    """Supportive student advisor with no function calling, just a chat"""
    st.header("❤︎ Student Support Chat")
    st.info("ⓘ In this section you can get personalized guidance, emotional support, and advice on study planning, degree selection, and CIF improvement. For direct links to resources, use Quick Search!")
    
    user_id = st.session_state.get("username", "demo_user")
    
    degree_reports = load_reports(user_id, "degree")
    grades_reports = load_reports(user_id, "grades")
    
    col1, col2 = st.columns(2)
    with col1:
        if degree_reports:
            degree_options = {f"Degree: {r.get('title', 'Untitled')}": r for r in degree_reports}
            selected_degree = st.selectbox(
                "☰ Select Degree:", 
                options=list(degree_options.keys()), 
                index=0,
                key="selected_degree"
            )
            selected_degree_data = degree_options[selected_degree]
        else:
            selected_degree_data = None
            st.info("⚠︎ No degree recommendations")
    
    with col2:
        if grades_reports:
            grades_options = {f"Grades: {r.get('title', 'Untitled')}": r for r in grades_reports}
            selected_grades = st.selectbox(
                "☰ Select Grades:", 
                options=list(grades_options.keys()), 
                index=0,
                key="selected_grades"
            )
            selected_grades_data = grades_options[selected_grades]
        else:
            selected_grades_data = None
            st.info("⚠︎ No grades analysis")
    
    # data summary
    data_summary = f"""Student Data ({user_id}):
• Degrees: {len(degree_reports)} available
• Grades: {len(grades_reports)} available"""
    
    # internal context for ai
    internal_context = f"""You have access to this student's data:

SELECTED DEGREE: {selected_degree_data.get('title', 'None') if selected_degree_data else 'None'}
Degree Content: {selected_degree_data.get('content', 'No degree recommendations yet') if selected_degree_data else 'No degree recommendations yet'}

SELECTED GRADES: {selected_grades_data.get('title', 'None') if selected_grades_data else 'None'}
Grades Content: {selected_grades_data.get('content', 'No grades uploaded yet') if selected_grades_data else 'No grades uploaded yet'}"""
    
    welcome_message = f"""Hi! I'm here to support you on your academic journey!

{data_summary}

I can help you with:  
✦ **Study planning** based on your grades and goals  
✦ **Degree selection advice** using your recommendations  
✦ **CIF improvement strategies** personalized to your level  
✦ **Emotional support** and motivation  
✦ **Resource suggestions** (names/topics - use Quick Search for links)  

What's on your mind today?"""
    
    if "student_resources_chat_history" not in st.session_state:
        st.session_state.student_resources_chat_history = [
            {"role": "assistant", "content": welcome_message}
        ]
    
    for msg in st.session_state.student_resources_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask for advice, support, or guidance..."):
        st.session_state.student_resources_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("𖦹 Thinking..."):
                enriched_prompt = f"""{internal_context}

User question: {prompt}

INSTRUCTIONS:
- Be supportive, empathetic, and encouraging
- Reference their degree recommendations and grades specifically when relevant
- Suggest study resources/scholarships by NAME only (e.g., "Try Khan Academy for biology")
- Help them make decisions about degrees, study plans, CIF improvement
- If they ask for links, tell them to use the Quick Search feature
- Focus on guidance and emotional support, not direct searches
- For Portuguese students (DGES system, nacional exams, CIF scores)"""
                
                response_text = GEMINI_CHAT.generate_content(
                    enriched_prompt,
                    user_id=user_id,
                    session_id="student_support_chat",
                    temperature=0.7
                )
                st.markdown(response_text)
        
        st.session_state.student_resources_chat_history.append({"role": "assistant", "content": response_text})
    
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⟲ Restart Chat", key="restart_chat_btn", width='stretch'):
            st.session_state.student_resources_chat_history = [
                {"role": "assistant", "content": welcome_message}
            ]
            st.rerun()
    
    with col2:
        if st.button("← Back to Quick Search", key="back_to_search_btn", width='stretch'):
            if "resources_mode" in st.session_state:
                del st.session_state.resources_mode
            st.rerun()


def render_student_resources():
    """Toggle Quick Search ↔ Support Chat"""
    if st.session_state.get("resources_mode") == "chat":
        render_student_resources_chat()
    else:
        render_student_main_resources()
