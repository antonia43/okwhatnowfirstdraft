import os
import json
import streamlit as st
import io
import PyPDF2
import docx2txt
from dotenv import load_dotenv
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
from datetime import datetime
from utils.database import save_report, save_user_cv, load_reports

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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract readable text from PDF bytes."""
    pdf_reader = None
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except:
        return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        return docx2txt.process(io.BytesIO(file_bytes))
    except:
        return ""

def safe_text_extract(file_bytes: bytes, file_name: str) -> str:
    """Safely extract text from any document type."""
    file_name = file_name.lower()
    
    if file_name.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif file_name.endswith(('.docx', '.doc')):
        return extract_text_from_docx(file_bytes)
    else:
        try:
            return str(file_bytes, 'utf-8', errors='ignore').strip()
        except:
            return ""

def _process_any_document(cv_text: str, prompt: str) -> str:
    """Process CV text with Langfuse Gemini."""
    GEMINI = LangfuseGeminiWrapper(
        api_key=os.getenv("GOOGLE_API_KEY"), 
        model="gemini-2.5-flash"
    )
    
    full_prompt = f"{prompt}\n\nCV DATA:\n{cv_text[:8000]}"
    
    response = GEMINI.generate_content(
        prompt=full_prompt,
        temperature=0.3,
        user_id=get_user_id(),
        session_id=get_session_id(),
        metadata={"type": "cv_feedback"}
    )
    
    if response and hasattr(response, 'strip'):
        return response.strip()
    return "No response"

def _extract_structured_from_document(uploaded_file, schema: dict):
    """Extract structured CV data - NO TRY/EXCEPT."""
    GEMINI = LangfuseGeminiWrapper(
        api_key=os.getenv("GOOGLE_API_KEY"), 
        model="gemini-2.5-flash"
    )
    
    # Reset file pointer and read bytes
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    
    # Extract readable TEXT
    cv_text = safe_text_extract(file_bytes, uploaded_file.name)
    
    if not cv_text or len(cv_text.strip()) < 50:
        return {
            "success": False, 
            "error": "No readable text found. Try a text-based PDF (not scanned image)."
        }
    
    st.info(f"Extracted {len(cv_text)} chars of text from {uploaded_file.name}")
    
    results = {}
    for key, question in schema.items():
        prompt = f"""
Extract ONLY this information from the CV below:
"{question}"

CV CONTENT:
{cv_text[:6000]}

Return ONLY the extracted value. If not found, return "Not found".
"""
        
        response = GEMINI.generate_content(
            prompt=prompt,
            temperature=0.1,
            user_id=get_user_id(),
            session_id=get_session_id(),
            metadata={"type": "cv_extraction", "field": key}
        )
        
        extracted = "Not found"
        if response:
            if hasattr(response, 'strip'):
                cleaned = response.strip().replace("``````", "")
                extracted = cleaned if cleaned else "Not found"
            else:
                extracted = str(response)[:500]
        
        results[key] = extracted
    
    return {"success": True, "data": results}

def render_cv_analysis():
    st.header("CV Analysis")
    
    user_id = st.session_state.get("username", "guest")
    
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
                    st.write(f"{key.replace('_', ' ').title()}: {value[:200]}{'...' if len(value) > 200 else ''}")
        else:
            st.error("CV not found in reports!")
            return
    
    else:
        uploaded = st.file_uploader(
            "Upload your CV (PDF, DOCX recommended)", 
            type=["pdf", "docx", "txt"],
            key="cv_upload_file"
        )
        
        if not uploaded:
            st.info("Upload your CV to get instant structured analysis!")
            st.markdown("""
            Tips for best results:
            - Use text-based PDFs (not scanned images)
            - DOCX files work perfectly
            - Max 10MB file size
            """)
            return
        
        with st.spinner("Analyzing your CV..."):
            st.success(f"Uploaded: {uploaded.name} ({uploaded.size/1024:.1f} KB)")
            

            results = _extract_structured_from_document(uploaded, CV_SCHEMA)
            
            if not results.get("success"):
                st.error(f"{results.get('error', 'Could not process CV.')}")
                st.info("Try: Convert to DOCX or use text-selectable PDF")
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
            

            save_user_cv(user_id, cv_data)
        

        st.subheader("Extracted Information")
        col1, col2 = st.columns(2)
        for i, (key, value) in enumerate(st.session_state.cv_data.items()):
            col = col1 if i % 2 == 0 else col2
            with col:
                st.markdown(f"{key.replace('_', ' ').title()}:")
                st.write(value[:300] + ("..." if len(value) > 300 else ""))
    

    st.subheader("Professional Feedback")
    
    if st.button("Generate Full Analysis", use_container_width=True, type="primary"):
        if not hasattr(st.session_state, 'cv_data'):
            st.error("No CV data available!")
            return
            
        with st.spinner("Generating professional analysis..."):
            cv_text = json.dumps(st.session_state.cv_data, indent=2, ensure_ascii=False)
            feedback_prompt = """
Analyze this CV data for job applications and provide:
1. Strengths - What stands out positively
2. Areas for Improvement - Actionable suggestions  
3. Overall Score - 1-10 with justification
4. Tailoring Tips - How to customize for target roles

Be specific, constructive, and professional.
"""
            
            feedback = _process_any_document(cv_text, feedback_prompt)
            st.session_state.current_feedback = feedback
        
        st.success("Analysis complete!")
    

    if hasattr(st.session_state, 'current_feedback') and st.session_state.current_feedback:
        st.markdown("---")
        st.success("Professional Analysis")
        st.markdown(st.session_state.current_feedback)
        

        if st.button("Save Analysis to Reports", use_container_width=True):
            report_id = save_report(
                user_id=user_id,
                report_type="professional_cv",
                title=f"CV Analysis - {st.session_state.cv_data.get('full_name', 'CV')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=st.session_state.current_feedback,
                cv_data=st.session_state.cv_data
            )
            st.success("Saved to My Reports!")
            st.rerun()
    

    if st.session_state.reports["professional_cv"]:
        with st.expander(f"Previous CV Analyses ({len(st.session_state.reports['professional_cv'])})", expanded=False):
            for report in st.session_state.reports["professional_cv"][:3]:
                with st.expander(report["title"]):
                    st.write(report.get("summary", "No summary")[:500] + "...")
                    if st.button(f"Load {report['title']}", key=f"load_{report['title']}"):
                        st.session_state.cv_data = report["cv_data"]
                        st.rerun()

