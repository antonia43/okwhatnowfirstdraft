import os
import json
import streamlit as st
import io
from dotenv import load_dotenv
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
from datetime import datetime
from utils.database import save_report, save_user_cv, load_reports
from google.genai import types

load_dotenv()

CV_SCHEMA = {
    "full_name": "What is the full name of the candidate?",
    "email": "What is the candidate's email address?",
    "phone": "What is the candidate's phone number?",
    "education": "List the candidate's education background.",
    "experience": "Summarize the candidate's professional experience.",
    "skills": "List the key technical and soft skills mentioned.",
    "languages": "Which languages does the candidate know?",
    "summary": "Summarize this CV in 3 sentences."
}

def _extract_structured_multimodal(uploaded_file, schema: dict):
    """Extract structured CV data using native multimodal processing."""
    GEMINI = LangfuseGeminiWrapper(
        api_key=os.getenv("GOOGLE_API_KEY"), 
        model="gemini-2.5-flash"
    )
    
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.pdf'):
        mime_type = 'application/pdf'
    elif file_name.endswith('.docx'):
        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file_name.endswith('.doc'):
        mime_type = 'application/msword'
    elif file_name.endswith('.png'):
        mime_type = 'image/png'
    elif file_name.endswith(('.jpg', '.jpeg')):
        mime_type = 'image/jpeg'
    else:
        mime_type = 'application/octet-stream'
    
    st.info(f"Processing {uploaded_file.name} as {mime_type}")
    
    results = {}
    for key, question in schema.items():
        prompt = f"""
Analyze this CV document and extract ONLY this information:
"{question}"

Return ONLY the extracted value. If not found, return "Not found".
"""
        
        try:
            response = GEMINI.generate_content_multimodal(
                prompt=prompt,
                file_data=file_bytes,
                mime_type=mime_type,
                temperature=0.1,
                user_id=get_user_id(),
                session_id=get_session_id(),
                metadata={"type": "cv_extraction", "field": key}
            )
            
            extracted = "Not found"
            if response:
                if hasattr(response, 'strip'):
                    cleaned = response.strip().replace("```", "")
                    extracted = cleaned if cleaned else "Not found"
                else:
                    extracted = str(response)[:500]
            
            results[key] = extracted
            
        except Exception as e:
            st.warning(f"Error extracting {key}: {str(e)}")
            results[key] = "Error"
    
    return {"success": True, "data": results}

def render_cv_analysis():
    st.header("CV Analysis")
    
    user_id = st.session_state.get("username", "guest")
    
    # Initialize feedback_saved flag
    if "feedback_saved" not in st.session_state:
        st.session_state.feedback_saved = False
    
    if "reports" not in st.session_state:
        st.session_state.reports = {}
    st.session_state.reports["professional_cv"] = load_reports(user_id, "professional_cv")
    
    cv_sources = ["Upload New CV"] + [r["title"] for r in st.session_state.reports["professional_cv"][:5]]
    source_choice = st.selectbox(
        "Choose CV source:", 
        cv_sources,
        key="cv_analysis_source_choice"
    )
    
    if source_choice != "Upload New CV":
        cv_report = next((r for r in st.session_state.reports["professional_cv"] 
                         if r["title"] == source_choice), None)
        if cv_report and cv_report.get("cv_data"):
            st.session_state.cv_data = cv_report["cv_data"]
            st.success(f"Loaded CV from: {source_choice}")
            
            st.subheader("Extracted CV Data")
            col1, col2 = st.columns(2)
            for i, (key, value) in enumerate(st.session_state.cv_data.items()):
                col = col1 if i % 2 == 0 else col2
                with col:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value[:200]}{'...' if len(value) > 200 else ''}")
        else:
            st.error("CV not found in reports!")
            return
    
    else:
        uploaded = st.file_uploader(
            "Upload your CV (PDF, DOCX, images supported)", 
            type=["pdf", "docx", "doc", "png", "jpg", "jpeg"],
            key="cv_upload_file"
        )
        
        if not uploaded:
            st.info("Upload your CV to get instant analysis!")
            st.markdown("""
            Supported formats:
            - PDFs (scanned or text-based)
            - DOCX/DOC files
            - Images (PNG, JPG, JPEG)
            - Analyzes text, images, tables, charts, and formatting
            """)
            return
        
        with st.spinner("𖦹 Analyzing your CV..."):
            st.success(f"Uploaded: {uploaded.name} ({uploaded.size/1024:.1f} KB)")
            
            results = _extract_structured_multimodal(uploaded, CV_SCHEMA)
            
            if not results.get("success"):
                st.error(f"{results.get('error', 'Could not process CV.')}")
                return
            
            cv_data = {
                "full_name": results["data"].get("full_name", "Not found"),
                "email": results["data"].get("email", ""),
                "phone": results["data"].get("phone", ""),
                "experience_summary": results["data"].get("experience", ""),
                "skills": results["data"].get("skills", ""),
                "education": results["data"].get("education", ""),
                "languages": results["data"].get("languages", ""),
                "summary": results["data"].get("summary", ""),
            }
            st.session_state.cv_data = cv_data
            
            # Save CV data to user profile
            save_user_cv(user_id, cv_data)
        
        st.subheader("Extracted Information")
        col1, col2 = st.columns(2)
        for i, (key, value) in enumerate(st.session_state.cv_data.items()):
            col = col1 if i % 2 == 0 else col2
            with col:
                st.markdown(f"**{key.replace('_', ' ').title()}:**")
                st.write(value[:300] + ("..." if len(value) > 300 else ""))
    
    st.markdown("---")
    st.subheader("Professional Feedback")
    
    if st.button("Generate Full Analysis", width="stretch", type="primary"):
        if not hasattr(st.session_state, 'cv_data'):
            st.error("No CV data available!")
            return
        
        # Reset saved flag when generating new analysis
        st.session_state.feedback_saved = False
            
        with st.spinner("Generating professional analysis..."):
            cv_text = json.dumps(st.session_state.cv_data, indent=2, ensure_ascii=False)
            feedback_prompt = f"""
Analyze this CV data for job applications and provide:

1. Strengths - What stands out positively
2. Areas for Improvement - Actionable suggestions  
3. Overall Score - Rate 1-10 with detailed justification
4. Tailoring Tips - How to customize for target roles

Be specific, constructive, and professional.

CV DATA:
{cv_text}
"""
            
            GEMINI = LangfuseGeminiWrapper(
                api_key=os.getenv("GOOGLE_API_KEY"), 
                model="gemini-2.5-flash"
            )
            
            feedback = GEMINI.generate_content(
                prompt=feedback_prompt,
                temperature=0.3,
                user_id=get_user_id(),
                session_id=get_session_id(),
                metadata={"type": "cv_feedback"}
            )
            
            st.session_state.current_feedback = feedback if feedback else "No feedback generated"
            
            # AUTO-SAVE: Save immediately after generation
            if st.session_state.current_feedback and not st.session_state.feedback_saved:
                try:
                    report_id = save_report(
                        user_id=user_id,
                        report_type="professional_cv",
                        title=f"CV Analysis - {st.session_state.cv_data.get('full_name', 'CV')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=st.session_state.current_feedback,
                        cv_data=st.session_state.cv_data
                    )
                    st.session_state.feedback_saved = True
                    st.success("✓ Analysis complete and saved to My Reports!")
                    st.balloons()
                except Exception as e:
                    st.warning(f"Analysis complete but couldn't auto-save: {e}")
            else:
                st.success("Analysis complete!")
                st.balloons()
        
        st.rerun()

    if hasattr(st.session_state, 'current_feedback') and st.session_state.current_feedback:
        st.markdown("---")
        st.markdown(st.session_state.current_feedback)
        
        if st.session_state.feedback_saved:
            st.info("🗂️ This analysis has been saved to My Reports")
        else:
            # manual save button as fallback (in case auto-save failed)
            if st.button("🗂️ Save to My Reports", width="stretch"):
                try:
                    report_id = save_report(
                        user_id=user_id,
                        report_type="professional_cv",
                        title=f"CV Analysis - {st.session_state.cv_data.get('full_name', 'CV')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=st.session_state.current_feedback,
                        cv_data=st.session_state.cv_data
                    )
                    st.session_state.feedback_saved = True
                    st.success("✓ Saved to My Reports!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save: {e}")
