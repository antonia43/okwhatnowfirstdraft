import streamlit as st
import os
from dotenv import load_dotenv
from services.langfuse_helper import LangfuseGeminiWrapper
from utils.database import get_saved_universities, load_reports
from services.tools import (
    render_exam_papers_tool,
    render_scholarships_tool,
    render_study_resources_tool,
    render_career_options_tool,
    render_wage_finder_tool
)
from services.student_tools import STUDENT_TOOLS, execute_function_call

load_dotenv()

GEMINI_CHAT = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash"
)

def render_student_main_resources():
    """Main resource hub with tool buttons"""
    st.header("✄ Student Resources")
    st.markdown("Explore tools and resources to help with your academic journey!")
    
    user_id = st.session_state.get("username", "demo_user")
    
    # Check if user has data
    has_data = False
    try:
        degree_reports = load_reports(user_id, "degree")
        grades_reports = load_reports(user_id, "grades")
        saved_unis = get_saved_universities(user_id)
        
        has_degree = len(degree_reports) > 0
        has_grades = len(grades_reports) > 0
        has_unis = len(saved_unis) > 0
        
        has_data = has_degree or has_grades or has_unis
        
        if has_data:
            st.success(f"✓ Loaded {len(degree_reports)} degrees, {len(grades_reports)} grades, {len(saved_unis)} unis")
        else:
            st.info("ⓘ Tip: For better personalized advice, try Degree Picker or Grades Analysis first!")
    except:
        pass
    
    st.divider()
    
    # Tool selection
    st.subheader("Choose a Tool:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Past Exam Papers", width="stretch", type="primary"):
            st.session_state.active_tool = "exams"
            st.rerun()
        
        if st.button("Study Resources", width="stretch", type="primary"):
            st.session_state.active_tool = "study"
            st.rerun()
    
    with col2:
        if st.button("Scholarships", width="stretch", type="primary"):
            st.session_state.active_tool = "scholarships"
            st.rerun()
        
        if st.button("Career Options", width="stretch", type="primary"):
            st.session_state.active_tool = "careers"
            st.rerun()
    
    with col3:
        if st.button("Wage Finder", width="stretch", type="primary"):
            st.session_state.active_tool = "wages"
            st.rerun()
        
        if st.button("❤︎ Support Chat", width="stretch"):
            st.session_state.resources_mode = "chat"
            st.rerun()
    
    st.divider()
    
    # Display selected tool
    if "active_tool" in st.session_state:
        if st.session_state.active_tool == "exams":
            render_exam_papers_tool()
        elif st.session_state.active_tool == "scholarships":
            render_scholarships_tool()
        elif st.session_state.active_tool == "study":
            render_study_resources_tool()
        elif st.session_state.active_tool == "careers":
            render_career_options_tool()
        elif st.session_state.active_tool == "wages":
            render_wage_finder_tool()


def render_student_resources_chat():
    """Supportive student advisor chat"""
    st.header("❤︎ Student Support Chat")
    st.info("Get personalized guidance, emotional support, and advice on study planning, degree selection, and academic improvement")
    
    user_id = st.session_state.get("username", "demo_user")
    
    # Load all user data
    degree_reports = load_reports(user_id, "degree")
    grades_reports = load_reports(user_id, "grades")
    saved_unis = get_saved_universities(user_id)
    
    # Split saved universities by type
    portuguese_unis = [uni for uni in saved_unis if uni.get('type') != 'International']
    international_unis = [uni for uni in saved_unis if uni.get('type') == 'International']
    
    col1, col2 = st.columns(2)
    with col1:
        if degree_reports:
            degree_options = {f"{r.get('title', 'Untitled')}": r for r in degree_reports}
            selected_degree = st.selectbox(
                "☰ Select Degree Picker Report:", 
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
    
    # Data summary with universities
    data_summary = f"""Student Data ({user_id}):
• Degrees: {len(degree_reports)} available
• Grades: {len(grades_reports)} available
• Saved Universities: {len(portuguese_unis)} Portuguese, {len(international_unis)} International"""
    
    # Format saved universities for context
    unis_context = ""
    if portuguese_unis:
        unis_context += "\n\nSAVED PORTUGUESE UNIVERSITIES:\n"
        for uni in portuguese_unis:
            unis_context += f"- {uni.get('name', 'N/A')}: {uni.get('program_name', 'N/A')} (Grade: {uni.get('average_grade_required', 'N/A')}, Location: {uni.get('location', 'N/A')})\n"
    
    if international_unis:
        unis_context += "\n\nSAVED INTERNATIONAL UNIVERSITIES:\n"
        for uni in international_unis:
            unis_context += f"- {uni.get('name', 'N/A')}: {uni.get('program_name', 'N/A')} (Location: {uni.get('location', 'N/A')})\n"
    
    if not saved_unis:
        unis_context = "\n\nSAVED UNIVERSITIES: None yet"
    
    # Internal context for AI
    internal_context = f"""You have access to this student's data:

SELECTED DEGREE: {selected_degree_data.get('title', 'None') if selected_degree_data else 'None'}
Degree Content: {selected_degree_data.get('content', 'No degree recommendations yet') if selected_degree_data else 'No degree recommendations yet'}

SELECTED GRADES: {selected_grades_data.get('title', 'None') if selected_grades_data else 'None'}
Grades Content: {selected_grades_data.get('content', 'No grades uploaded yet') if selected_grades_data else 'No grades uploaded yet'}
{unis_context}"""
    
    welcome_message = f"""Hi! I'm here to support you on your academic journey!

{data_summary}

I can help you with:  
✦ **Study planning** based on your grades and goals  
✦ **Degree selection advice** using your recommendations  
✦ **University choices** from your saved list  
✦ **Academic improvement strategies** personalized to your level  
✦ **Emotional support** and motivation  
✦ **Career guidance** and application tips  

What's on your mind today?"""
    
    if "student_resources_chat_history" not in st.session_state:
        st.session_state.student_resources_chat_history = [
            {"role": "assistant", "content": welcome_message}
        ]
    
    for msg in st.session_state.student_resources_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask for advice..."):
        st.session_state.student_resources_chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # FUNCTION CALLING ENABLED
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"""You're a supportive student advisor with access to the student's data through tools.

User ID: {user_id}

Student question: {prompt}

INSTRUCTIONS:
- Use tools to access their saved universities, grades, and profile
- Give personalized advice based on their actual data
- Be supportive and encouraging
- Reference specific universities and grades when relevant""",
                    config=types.GenerateContentConfig(
                        tools=CAREER_CORNER_TOOLS,
                        temperature=0.7
                    )
                )
                
                # Handle function calls
                while response.candidates[0].content.parts:
                    part = response.candidates[0].content.parts[0]
                    
                    # Check if it's a function call
                    if hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        st.caption(f"🔧 Using tool: {func_call.name}")
                        
                        # Execute function
                        func_result = execute_function_call(
                            func_call.name,
                            dict(func_call.args)
                        )
                        
                        # Send result back to Gemini
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[
                                {"role": "user", "parts": [{"text": prompt}]},
                                {"role": "model", "parts": [part]},
                                {"role": "function", "parts": [{
                                    "function_response": {
                                        "name": func_call.name,
                                        "response": func_result
                                    }
                                }]}
                            ],
                            config=types.GenerateContentConfig(
                                tools=CAREER_CORNER_TOOLS,
                                temperature=0.7
                            )
                        )
                    else:
                        # Final text response
                        response_text = response.text
                        st.markdown(response_text)
                        st.session_state.student_resources_chat_history.append({
                            "role": "assistant",
                            "content": response_text
                        })
                        break

def render_student_resources():
    """Main entry point - toggle between tools and chat"""
    if st.session_state.get("resources_mode") == "chat":
        render_student_resources_chat()
    else:
        render_student_main_resources()

