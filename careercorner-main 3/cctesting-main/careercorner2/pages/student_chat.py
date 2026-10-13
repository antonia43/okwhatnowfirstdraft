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
    
    st.header("Chat with Career Corner's AI Assistant!")

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
            st.session_state.student_chat_history = []
            st.session_state.conversation_turn = 0
            st.session_state.recommended_option = None
            if "last_trace_ids" in st.session_state:
                st.session_state.last_trace_ids = []
            st.rerun()

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        st.error("GOOGLE_API_KEY not found in your .env file.")
        return

    # initializing Langfuse-wrapped Gemini client
    gemini_client = LangfuseGeminiWrapper(
        api_key=api_key,
        model="gemini-2.5-flash"
    )

    # getting user and session IDs for tracing
    user_id = get_user_id()
    session_id = get_session_id()
    
    # initialising conversation counter
    if "conversation_turn" not in st.session_state:
        st.session_state.conversation_turn = 0
    
    if "student_chat_history" not in st.session_state:
        st.session_state.student_chat_history = []

    user_input = st.chat_input("Ask Career Corner Assistant anything about your studies!")
    
    if user_input:
        st.session_state.conversation_turn += 1
        st.session_state.student_chat_history.append({
            "role": "user", 
            "content": user_input
        })
        
        # building conversation context for the AI
        conversation_context = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in st.session_state.student_chat_history[-4:] #last 4 messages for context
        ])

        system_instruction = f"""You are Career Corner Assistant, a friendly career counselor.

**STRICT RULES:**
1. Ask 5+ natural questions FIRST - NO tool names before turn 6
2. NEVER mention tool names during conversation
3. Turn 6+: "**[TOOL NAME]** would suit you best because [reason]" → then STOP

Have completely natural conversations. Ask whatever feels right.

**Understand their needs silently:**
- Grades/performance talk → Grades Analysis (turn 6+)
- Career confusion → Career Quiz (turn 6+)  
- Degree/program → Degree Picker (turn 6+)
- Universities → University Finder (turn 6+)
- Jobs/work → Job Recommendations (turn 6+)

Current turn: {st.session_state.conversation_turn}
Previous context:
{conversation_context}
"""

        try:
            # generating response with langfuse tracing
            ai_message = gemini_client.generate_content(
                prompt=user_input,
                system_instruction=system_instruction,
                temperature=0.4,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "conversation_type": "student_dashboard_assistant",
                    "user_type": "student",
                    "turn": st.session_state.conversation_turn,
                    "message_count": len(st.session_state.student_chat_history)
                }
            )
            
            # storing the trace id for potential feedback
            current_trace_id = gemini_client.last_trace_id
            if "last_trace_ids" not in st.session_state:
                st.session_state.last_trace_ids = []
            st.session_state.last_trace_ids.append(current_trace_id)
            
        except Exception as e:
            ai_message = f"Error: {e}"
            st.error("Something went wrong. Please try again.")

        st.session_state.student_chat_history.append({
            "role": "assistant", 
            "content": ai_message
        })

        # checking if AI made a recommendation
        options = ["Career Quiz", "Grades Analysis", "Job Recommendations"]
        matched = [opt for opt in options if opt in ai_message]

        if len(matched) == 1 and "would suit you best" in ai_message.lower():
            st.session_state.recommended_option = matched[0]
            # logging successful recommendation to langfuse
            if current_trace_id:
                log_user_feedback(
                    current_trace_id, 
                    score=1.0, 
                    comment=f"Recommended: {matched[0]} after {st.session_state.conversation_turn} turns"
                )
        else:
            st.session_state.recommended_option = None
        
        # Check if AI suggested professional dashboard
        if "professional dashboard" in ai_message.lower():
            st.session_state.show_professional_redirect = True

    # displaying messages with feedback buttons
    for idx, msg in enumerate(st.session_state.student_chat_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            '''# Add feedback buttons for assistant messages
            if msg["role"] == "assistant":
                assistant_message_index = idx // 2
                
                if "last_trace_ids" in st.session_state and assistant_message_index < len(st.session_state.last_trace_ids):
                    trace_id = st.session_state.last_trace_ids[assistant_message_index]
                    
                    col1, col2, col3 = st.columns([1, 1, 10])
                    with col1:
                        if st.button("👍", key=f"thumbs_up_{idx}"):
                            log_user_feedback(trace_id, score=1.0, comment="Helpful response")
                            st.success("Thanks!")
                    with col2:
                        if st.button("👎", key=f"thumbs_down_{idx}"):
                            log_user_feedback(trace_id, score=0.0, comment="Not helpful")
                            st.warning("Thanks for your feedback!")'''

    # showing redirect button if recommendation exists
    if st.session_state.get("recommended_option") and st.session_state.get("student_choice") != st.session_state.recommended_option:
        st.markdown("---")
        st.success(f"⟡ Ready to get started with **{st.session_state.recommended_option}**?")
        
        def redirect_to_option():
            st.session_state.redirect_to = st.session_state.recommended_option
            st.session_state.recommended_option = None
            st.session_state.conversation_turn = 0
        
        if st.button(f"Take me to {st.session_state.recommended_option}", width='stretch', on_click=redirect_to_option):
            st.rerun()
    
    # showing professional dashboard redirect if suggested
    if st.session_state.get("show_professional_redirect", False):
        st.markdown("---")
        st.info("✴ Based on your experience, the Professional Dashboard might be more helpful!")
        col1, col2 = st.columns(2)
        
        def go_to_professional():
            st.session_state.user_type = "professional"
            st.session_state.show_professional_redirect = False
            st.session_state.conversation_turn = 0
        
        def stay_student():
            st.session_state.show_professional_redirect = False
        
        with col1:
            if st.button("Go to Professional Dashboard", width='stretch', on_click=go_to_professional):
                st.rerun()
        with col2:
            if st.button("Stay on Student Dashboard", width='stretch', on_click=stay_student):
                st.rerun()
