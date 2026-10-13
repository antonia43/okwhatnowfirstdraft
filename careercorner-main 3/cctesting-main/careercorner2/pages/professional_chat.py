import os
import streamlit as st
from dotenv import load_dotenv
from services.langfuse_helper import (
    LangfuseGeminiWrapper,
    get_user_id,
    get_session_id,
    log_user_feedback,
)

load_dotenv()

def render_dashboard_chat():
    """Rendering the AI-powered dashboard chat interface"""
    
    st.subheader("Chat with Career Corner's AI Assistant!")

    typewriter_html = """
    <style>
    .typewriter {
        font-family: monospace;
        overflow: hidden;
        border-right: .15em solid orange;
        white-space: nowrap;
        animation: typing 2s steps(40, end), blink-caret .75s step-end infinite;
    }
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: orange; }
    }
    </style>

    <p class="typewriter">Pick an option from the side bar to start your journey!
    If you're still unsure what option to pick, let me help you!</p>
    """
    st.markdown(typewriter_html, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("⟲ Start Over"):
            st.session_state.professional_chat_history = []
            st.session_state.conversation_turn = 0
            st.session_state.recommended_option = None
            if "professional_trace_ids" in st.session_state:
                st.session_state.professional_trace_ids = []
            st.rerun()

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        st.error("GOOGLE_API_KEY not found in your .env file.")
        return

    gemini_client = LangfuseGeminiWrapper(
        api_key=api_key,
        model="gemini-2.5-flash"
    )
    
    user_id = get_user_id()
    session_id = get_session_id()
    
    if "conversation_turn" not in st.session_state:
        st.session_state.conversation_turn = 0
    
    if "professional_chat_history" not in st.session_state:
        st.session_state.professional_chat_history = []

    user_input = st.chat_input("Ask Career Corner Assistant anything about your career!", key="prof_chat_input")
    
    if user_input:
        st.session_state.conversation_turn += 1
        st.session_state.professional_chat_history.append({
            "role": "user", 
            "content": user_input
        })

        conversation_context = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in st.session_state.professional_chat_history[-4:]
        ])

        system_instruction = f"""You are Career Corner Assistant, a friendly career counselor.

**STRICT RULES:**
1. Ask 5+ natural questions FIRST - NO tool names before turn 6
2. NEVER mention tool names during conversation  
3. Turn 6+: "**[TOOL NAME]** would suit you best because [reason]" → then STOP

Have completely natural conversations like talking to a colleague about career.

**Understand their needs silently (don't ask about tools):**
- CV/resume talk → CV Analysis
- Career confusion/next steps → Career Growth
- Job search/resources → Your Next Steps
- Interviews/practice → Interview Prep
- Build/tailor CV → CV Builder
- Past work/reports → My Reports

TOOLS (recommend ONLY after 5 questions): CV Analysis, Career Growth, Your Next Steps, Interview Prep, CV Builder, My Reports

Current turn: {st.session_state.conversation_turn}
Previous context:
{conversation_context}
"""

        try:
            ai_message = gemini_client.generate_content(
                prompt=user_input,
                system_instruction=system_instruction,
                temperature=0.4,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "conversation_type": "professional_dashboard_assistant",
                    "user_type": "professional",
                    "turn": st.session_state.conversation_turn,
                    "message_count": len(st.session_state.professional_chat_history)
                }
            )
            
            current_trace_id = gemini_client.last_trace_id
            if "professional_trace_ids" not in st.session_state:
                st.session_state.professional_trace_ids = []
            st.session_state.professional_trace_ids.append(current_trace_id)
            
        except Exception as e:
            ai_message = f"Error: {e}"
            st.error("Something went wrong. Please try again.")

        st.session_state.professional_chat_history.append({
            "role": "assistant", 
            "content": ai_message
        })

        options = ["CV Analysis", "Career Growth", "Your Next Steps", "Interview Prep", "CV Builder", "My Reports"]
        matched = [opt for opt in options if opt in ai_message]

        if len(matched) == 1 and "would suit you best" in ai_message.lower():
            st.session_state.recommended_option = matched[0]
            if current_trace_id:
                log_user_feedback(
                    current_trace_id, 
                    score=1.0, 
                    comment=f"Recommended: {matched[0]} after {st.session_state.conversation_turn} turns"
                )
        else:
            st.session_state.recommended_option = None
        
        if "student dashboard" in ai_message.lower():
            st.session_state.show_student_redirect = True

    for idx, msg in enumerate(st.session_state.professional_chat_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.get("recommended_option") and st.session_state.professional_choice != st.session_state.recommended_option:
        st.markdown("---")
        st.success(f"⟡ Ready to get started with **{st.session_state.recommended_option}**?")
        
        def redirect_to_option():
            st.session_state.redirect_to = st.session_state.recommended_option
            st.session_state.recommended_option = None
            st.session_state.conversation_turn = 0
        
        if st.button(f"Take me to {st.session_state.recommended_option}", width='stretch', on_click=redirect_to_option, key="prof_redirect_btn"):
            st.rerun()
    
    if st.session_state.get("show_student_redirect", False):
        st.markdown("---")
        st.info("★ Based on your situation, the Student Dashboard might be more helpful!")
        col1, col2 = st.columns(2)
        
        def go_to_student():
            st.session_state.user_type = "student"
            st.session_state.show_student_redirect = False
            st.session_state.conversation_turn = 0
        
        def stay_professional():
            st.session_state.show_student_redirect = False
        
        with col1:
            if st.button("Go to Student Dashboard", width='stretch', on_click=go_to_student, key="go_student_btn"):
                st.rerun()
        with col2:
            if st.button("Stay on Professional Dashboard", width='stretch', on_click=stay_professional, key="stay_prof_btn"):
                st.rerun()

