import streamlit as st
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
import os
import re
from dotenv import load_dotenv
import json
import pandas as pd
from utils.database import save_report, load_reports
from datetime import datetime
from pages.university_finder import normalize_text
import base64
import mimetypes

load_dotenv()

GRADES_MODEL = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)

def render_grades_analysis():
    """Main grades analysis function"""
    
    st.header("⛶ Grades Analysis")
    
    if "grades_input_method" not in st.session_state:
        st.session_state.grades_input_method = None
    if "student_type" not in st.session_state:
        st.session_state.student_type = None
    if "student_grades_data" not in st.session_state:
        st.session_state.student_grades_data = None
    if "grades_calculation_weights" not in st.session_state:
        st.session_state.grades_calculation_weights = None
    if "final_grade_calculated" not in st.session_state:
        st.session_state.final_grade_calculated = False
    
    # Step 1: Choose student type (Portuguese or International)
    if st.session_state.student_type is None:
        render_student_type_selection()
        return
    
    # Step 2: Choose input method (Manual or Upload)
    if st.session_state.student_grades_data is None:
        if st.session_state.grades_input_method is None:
            render_input_method_selection()
        elif st.session_state.grades_input_method == "manual":
            if st.session_state.student_type == "portuguese":
                render_manual_grades_input()
            else:
                render_international_grades_input()
        elif st.session_state.grades_input_method == "upload":
            render_file_upload_grades()
    
    # Step 3: Calculate final grade (Portuguese only)
    elif not st.session_state.final_grade_calculated:
        if st.session_state.student_type == "portuguese":
            calculate_and_save_grade()
        else:
            # International students skip calculation, go straight to saving
            save_international_grades()
    
    # Step 4: Show results
    else:
        show_final_results()


def render_student_type_selection():
    """Choose between Portuguese or International student"""
    st.info("First: Choose your profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Portuguese Student  
        ✦ Portuguese secondary education  
        ✦ DGES-compatible calculation  
        ✦ Course comparison with universities  
        """)
        if st.button("I'm a Portuguese Student", width='stretch', type="primary", key="btn_portuguese"):
            st.session_state.student_type = "portuguese"
            st.rerun()
    
    with col2:
        st.markdown("""
        ### International Student  
        ✦ Any international curriculum  
        ✦ Grade storage for university search  
        ✦ No DGES calculation needed  
        """)
        if st.button("I'm an International Student", width='stretch', type="primary", key="btn_international"):
            st.session_state.student_type = "international"
            st.rerun()

def render_input_method_selection():
    """Choose input method based on student type"""
    student_type = st.session_state.student_type
    
    if student_type == "portuguese":
        st.info("Portuguese Student: Enter your grades manually")
        
        st.markdown("""
        **✍︎ Manual Entry**
        - Guided grade entry
        - Select subjects one by one
        - Full control over data
        - 5 minutes
        """)
        
        if st.button("✍︎ Start Manual Entry", width="stretch", type="primary", key="btn_manual_entry"):
            st.session_state.grades_input_method = "manual"
            st.rerun()
    
    else:  # international
        st.info("International Student: Upload your transcript")
        
        st.markdown("""
        **➜] Upload Document**
        - Upload transcript/report card
        - AI extracts grades automatically
        - Supports PDF, JPG, PNG
        - 2 minutes
        """)
        
        if st.button("➜] Upload Document", width="stretch", type="primary", key="btn_upload_entry"):
            st.session_state.grades_input_method = "upload"
            st.rerun()
    
    if st.button("← Back to Student Type", width="stretch", key="btn_back_to_student_type"):
        st.session_state.student_type = None
        st.rerun()
        
def save_international_grades():
    """Save international grades to database without calculation"""
    grades_data = st.session_state.student_grades_data
    
    st.success("✓ Grades collected!")
    
    st.subheader("☰ Your Grades Summary")
    
    subjects = grades_data.get("subjects", [])
    
    if subjects:
        st.write(f"Total Subjects: {len(subjects)}")
        st.write(f"Country: {grades_data.get('country', 'International')}")
        st.write(f"Grade Scale: {grades_data.get('grade_scale', 'Various')}")
        
        with st.expander("View All Subjects"):
            for subj in subjects:
                st.write(f"- {subj['name']}: {subj['grade']} ({subj.get('year', 'N/A')})")
    
    if "username" in st.session_state and st.session_state["username"]:
        try:
            report_content = json.dumps({
                "student_type": "international",
                "grades_data": grades_data,
                "saved_at": datetime.now().isoformat()
            })
            
            save_report(
                user_id=st.session_state["username"],
                report_type="grades",
                title=f"International Grades - {grades_data.get('country', 'International')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=report_content,
                cv_data=None
            )
            
            st.success("🗂️ Grades saved to My Reports!")
            st.session_state.final_grade_calculated = True
            
            st.info("Next Steps: Use your saved grades in University Finder to find matching programs!")
            
            st.markdown("---")
            
            # AI OVERVIEW BUTTON (INTERNATIONAL ONLY)
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⟡ Get AI Overview", width='stretch', type="primary", key="btn_ai_overview"):
                    with st.spinner("Analyzing your grades..."):
                        overview = generate_international_grades_overview(grades_data)
                        if overview:
                            st.markdown("---")
                            st.subheader("☰ Your Academic Profile")
                            st.markdown(overview)
            
            with col2:
                if st.button("↻ Add More Grades", width='stretch', key="btn_add_more"):
                    reset_grades_analysis()
                    st.rerun()
            
        except Exception as e:
            st.error(f"⚠ Could not save grades: {e}")


def generate_international_grades_overview(grades_data: dict) -> str:
    """Generate AI overview of international student's strengths, weaknesses, and degree suggestions"""
    try:
        subjects = grades_data.get("subjects", [])
        country = grades_data.get("country", "International")
        grade_scale = grades_data.get("grade_scale", "Unknown")
        
        # Format subjects for AI
        subjects_text = "\n".join([
            f"- {subj['name']}: {subj['grade']} ({subj.get('year', 'N/A')})"
            for subj in subjects
        ])
        
        prompt = f"""Analyze this international student's academic profile and provide insights.

**Student Profile:**
- Country: {country}
- Grade Scale: {grade_scale}
- Total Subjects: {len(subjects)}

**Grades:**
{subjects_text}

**Provide a structured analysis:**

## Academic Strengths
[Identify 3-4 subjects where the student excels and what this indicates about their skills]

## Areas for Improvement
[Identify 2-3 subjects that could be improved and provide constructive advice]

## Recommended Degree Paths
[Based on their grades, suggest 4-5 specific degree programs they would be well-suited for. Be specific with degree names.]

## Study Tips
[2-3 actionable tips to improve in weaker areas]

---

**FORMATTING RULES:**
- Use markdown headers (##) and bullet points
- Be encouraging and constructive
- Focus on specific, actionable insights
- Suggest degrees that match their strongest subjects
- Keep it concise (under 400 words total)
"""
        
        response = GRADES_MODEL.generate_content(
            prompt=prompt,
            user_id=get_user_id(),
            session_id=get_session_id(),
            temperature=0.7,
            metadata={"type": "international_grades_overview"}
        )
        
        return response
        
    except Exception as e:
        st.error(f"Could not generate overview: {e}")
        return None
           

def render_file_upload_grades():
    """Upload and extract grades from file - supports both Portuguese and International"""
    
    st.subheader("➜ Upload Your Grades Document")
    
    if st.button("← Back", key="btn_back_from_file_upload", width='stretch'):
        st.session_state.grades_input_method = None
        st.rerun()
    
    student_type = st.session_state.student_type
    
    if student_type == "portuguese":
        st.info("ⓘ **Portuguese Student**: Upload your transcript, report card, or grades sheet.")
    else:
        st.info("ⓘ **International Student**: Upload any transcript or report card in any language!")
    
    st.write("**Supported formats:** PDF, JPG, PNG, JPEG")
    
    uploaded_file = st.file_uploader(
        "Choose your document",
        type=["pdf", "jpg", "png", "jpeg"],
        help="We'll extract your grades automatically using AI"
    )
    
    if uploaded_file:
        st.success(f"✓ Uploaded: {uploaded_file.name}")
        
        file_extension = uploaded_file.name.split('.')[-1].lower()
        temp_filename = f"temp_grades.{file_extension}"
        
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.read())
        
        if file_extension in ['jpg', 'jpeg', 'png']:
            st.image(temp_filename, caption="Uploaded Document", width="stretch")
        
        # Extract button
        if st.button("⟡ Extract Grades", width='stretch', type="primary", key="btn_extract_grades"):
            with st.spinner("Analyzing document and extracting grades... This may take a moment!"):
                extracted_data = extract_grades_from_file(temp_filename, student_type)
            
            if extracted_data:
                # ✅ SAVE TO SESSION STATE IMMEDIATELY
                st.session_state.extracted_grades_preview = extracted_data
                st.success("✓ Grades extracted successfully!")
                st.rerun()
            else:
                st.error("⚠ Could not extract grades from this file.")
                st.write("**Possible reasons:**")
                st.write("- Image quality is too low")
                st.write("- Text is not clear or readable")
                st.write("- Format is not recognized")
                
                if st.button("✎ Try Manual Entry Instead", width='stretch', key="btn_manual_after_failed_extract"):
                    st.session_state.grades_input_method = "manual"
                    st.rerun()
    

    # ✅ SHOW PREVIEW IF EXISTS (outside button click)
    if "extracted_grades_preview" in st.session_state and st.session_state.extracted_grades_preview:
        extracted_data = st.session_state.extracted_grades_preview
        
        st.markdown("---")
        st.subheader("☰ Extracted Information")
        
        # Show preview based on type
        if extracted_data.get("student_type") == "portuguese":
            st.write(f"**Current Year:** {extracted_data.get('current_year', 'Unknown')}")
            st.write(f"**Track:** {extracted_data.get('track', 'Unknown')}")
            
            with st.expander("View Extracted Grades"):
                grades = extracted_data.get("grades", {})
                for year in ["10th", "11th", "12th"]:
                    if grades.get(year):
                        st.write(f"**{year} Grade:**")
                        for subj, grade in grades[year].items():
                            if grade > 0:
                                st.write(f"  - {subj}: {grade}")
                
                if grades.get("exams"):
                    st.write("**National Exams:**")
                    for exam, grade in grades["exams"].items():
                        if grade > 0:
                            st.write(f"  - {exam}: {grade}")
        else:
            st.write(f"**Country:** {extracted_data.get('country', 'Unknown')}")
            st.write(f"**Grade Scale:** {extracted_data.get('grade_scale', 'Unknown')}")
            st.write(f"**Number of Subjects:** {len(extracted_data.get('subjects', []))}")
            
            with st.expander("View Extracted Subjects"):
                # Group by subject name for cleaner display
                subjects = extracted_data.get('subjects', [])
                grouped = {}
                for subj in subjects:
                    name = subj['name'].replace(' Q1', '').replace(' Q2', '').replace(' Q3', '')
                    if name not in grouped:
                        grouped[name] = []
                    grouped[name].append(subj['grade'])
                
                for subject_name, grades in grouped.items():
                    st.write(f"- **{subject_name}**: {', '.join(grades)}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✓ Confirm & Continue", width='stretch', type="primary", key="btn_confirm_extracted"):
                st.session_state.student_grades_data = extracted_data
                st.session_state.pop("extracted_grades_preview", None)  # Clean up
                st.rerun()
        
        with col2:
            if st.button("✎ Edit Manually Instead", width='stretch', key="btn_edit_extracted_manually"):
                st.session_state.grades_input_method = "manual"
                
                # Pre-fill manual entry with extracted data
                if extracted_data.get("student_type") == "portuguese":
                    st.session_state.temp_grades = extracted_data.get("grades", {})
                else:
                    st.session_state.temp_intl_grades = extracted_data.get("subjects", [])
                
                st.session_state.pop("extracted_grades_preview", None)  # Clean up
                st.rerun()


def extract_grades_from_file(file_path: str, student_type: str):
    """Extract grades from uploaded file using Gemini vision multimodal"""
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'image/jpeg' if file_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        
        if student_type == "portuguese":
            prompt = """Analyze this PORTUGUESE student transcript and extract ALL grades.
Return ONLY valid JSON in this exact format:
{
  "student_type": "portuguese",
  "current_year": "10th Grade / 11th Grade / 12th Grade (In Progress) / 12th Grade (Completed)",
  "track": "Ciências e Tecnologias / Ciências Socioeconómicas / Línguas e Humanidades / Artes Visuais",
  "grades": {
    "10th": {"Português": 15, "Matemática A": 17, "Inglês": 16, ...},
    "11th": {"Português": 16, "Física e Química A": 18, ...},
    "12th": {"Português": 17, ...},
    "exams": {"Português (639)": 150, "Matemática A (635)": 170, ...}
  }
}

Rules:
- Extract ALL visible subjects and grades
- Grades are 0-20 scale for subjects, 0-200 for exams
- If year or track unclear, make best guess
- Return ONLY JSON, no explanations"""
        else:
            prompt = """Analyze this INTERNATIONAL student transcript and extract ALL grades.
Return ONLY valid JSON in this exact format:
{
  "student_type": "international",
  "country": "country name or Unknown",
  "grade_scale": "e.g., 0-100, A-F, 1-5",
  "subjects": [
    {"name": "Mathematics", "grade": "95", "year": "11th Grade"},
    {"name": "Physics", "grade": "A", "year": "12th Grade"},
    {"name": "Chemistry", "grade": "4.0", "year": "10th Grade"}
  ],
  "current_year": "best guess of student's current year",
  "school_type": "if visible (IB, A-Levels, etc.)"
}

Rules:
- Extract ALL visible subjects with their exact grades
- Keep grade format as shown (numbers, letters, GPA)
- If year not shown, use "N/A"
- Return ONLY JSON, no explanations"""
        
        # USE MULTIMODAL METHOD HERE ✅
        raw = GRADES_MODEL.generate_content_multimodal(
            prompt=prompt,
            file_data=file_bytes,
            mime_type=mime_type,
            user_id=get_user_id(),
            session_id=get_session_id(),
            temperature=0.1,
            metadata={"type": "grades_extraction"}
        )
        
        text = raw.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(text)
        
        # Return structured data based on type
        if data.get("student_type") == "portuguese":
            return {
                "student_type": "portuguese",
                "current_year": data.get("current_year", "12th Grade (Completed)"),
                "track": data.get("track", "Ciências e Tecnologias"),
                "grades": data.get("grades", {}),
                "input_method": "upload"
            }
        else:
            return {
                "student_type": "international",
                "input_method": "upload",
                "country": data.get("country", "Unknown"),
                "grade_scale": data.get("grade_scale", "Unknown"),
                "subjects": data.get("subjects", []),
                "current_year": data.get("current_year", ""),
                "school_type": data.get("school_type", "")
            }
            
    except json.JSONDecodeError as e:
        st.error(f"⚠ Could not parse AI response: {e}")
        return None
    except Exception as e:
        st.error(f"⚠ Error extracting grades: {e}")
        return None


def render_international_grades_input():
    """International student manual grade entry"""
    st.subheader("✍︎ International Grades Entry")
    
    if st.button("← Back to Input Method Selection", key="btn_back_from_intl_entry", width="stretch"):
        st.session_state.grades_input_method = None
        st.rerun()
    
    
    st.info("ⓘ Enter all your subjects and grades. We'll analyze them and provide guidance.")
    
    # initializing temporary data
    if "temp_intl_grades" not in st.session_state:
        st.session_state.temp_intl_grades = []
    
    # Country and grading system
    col1, col2 = st.columns(2)
    with col1:
        country = st.text_input("Country", placeholder="e.g., USA, UK, India", key="intl_country")
    with col2:
        grade_scale = st.text_input("Grade Scale", placeholder="e.g., 0-100, A-F, 1-10", key="intl_scale")
    
    
    # subject input form
    with st.form("intl_grades_form", clear_on_submit=True):
        st.write("**Add Subject:**")
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            subject_name = st.text_input("Subject Name", placeholder="e.g., Mathematics, Physics", label_visibility="collapsed")
        with col2:
            grade_input = st.text_input("Grade", placeholder="e.g., 95, A, 4.0", label_visibility="collapsed")
        with col3:
            year = st.selectbox("Year", ["9th", "10th", "11th", "12th", "N/A"], key="intl_year", label_visibility="collapsed")
        
        submitted = st.form_submit_button("+ Add Subject", width="stretch")
        
        if submitted and subject_name.strip() and grade_input.strip():
            new_subject = {
                "name": subject_name.strip(),
                "grade": grade_input.strip(),
                "year": year
            }
            st.session_state.temp_intl_grades.append(new_subject)
            st.success(f"✓ Added: {subject_name}")
    
    # displaying current subjects
    if st.session_state.temp_intl_grades:
        st.subheader(f"{len(st.session_state.temp_intl_grades)} Subjects Added")
        
        for i, subj in enumerate(st.session_state.temp_intl_grades):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{subj['name']}**")
            with col2:
                st.write(f"{subj['grade']}")
            with col3:
                st.write(f"({subj['year']})")
            with col4:
                if st.button("🗑", key=f"del_intl_{i}", width="stretch"):
                    st.session_state.temp_intl_grades.pop(i)
                    st.rerun()
        
        
        # saving
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Save & Continue", width="stretch", type="primary", key="btn_save_intl"):
                st.session_state.student_grades_data = {
                    "student_type": "international",
                    "input_method": "manual",
                    "subjects": st.session_state.temp_intl_grades,
                    "country": country or "International",
                    "grade_scale": grade_scale or "Various"
                }
                st.rerun()
        
        with col2:
            if st.button("🗑 Clear All", width="stretch", key="btn_clear_intl"):
                st.session_state.temp_intl_grades = []
                st.rerun()
    
    else:
        st.info("↑ Add your first subject above to get started!")



def reset_grades_analysis():
    """Reset all grades analysis state"""
    keys_to_reset = [
        "grades_input_method",
        "student_type",
        "student_grades_data",
        "grades_calculation_weights",
        "final_grade_calculated",
        "temp_grades",
        "temp_intl_grades",
        "student_final_grade",
        "custom_subjects"
    ]
    for key in keys_to_reset:
        st.session_state.pop(key, None)


def calculate_and_save_grade():
    """Calculating final admission average and save to reports"""
    
    st.subheader("% Calculate Your Admission Average")
    
    grades_data = st.session_state.student_grades_data
    current_year = grades_data.get("current_year", "12th Grade (Completed)")
    

    
    
    # checking if stuedent has exam grades
    has_exams = False
    exams = grades_data.get("grades", {}).get("exams", {})
    has_exams = any(score > 0 for score in exams.values())
    
    # special handling for 10th graders
    if "10th" in current_year:
        st.info("ⓘ **10th Grade:** You haven't taken national exams yet. Your grade will be based 100% on your school grades.")
        
        weights = {'secondary': 1.0, 'exam': 0.0}
        
        
        # calculate button
        if st.button("⟡ Calculate My Current Average", width='stretch', type="primary", key="btn_calculate_final_grade"):
            st.session_state.grades_calculation_weights = weights
            
            final_grade = calculate_admission_average(grades_data, weights)
            st.session_state.student_final_grade = final_grade
            
            if "username" in st.session_state and st.session_state.username:
                report_content = generate_simple_grade_report(grades_data, final_grade, weights)
                
                try:
                    save_report(
                        user_id=st.session_state.username,
                        report_type="grades",
                        title=f"Grades - CIF {final_grade:.1f}/20 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=json.dumps({
                            "student_grades_data": st.session_state.student_grades_data,
                            "final_cif": float(final_grade),
                            "weights_used": weights,
                            "summary": report_content
                        }),
                        cv_data=None
                    )
                    st.session_state.final_grade_calculated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save: {e}")
        
        return  # exit early for 10th graders
    
    # for 11th and 12th graders, to choose calculation method
    st.subheader("⚖ Choose Calculation Method")
    
    if not has_exams:
        st.warning("⚠︎ **No exam grades entered.** We'll calculate based on your secondary school grades only!")
        weights = {'secondary': 1.0, 'exam': 0.0}
    else:
        st.write("Different universities use different formulas:")
        
        weight_option = st.radio(
            "Calculation method:",
            [
                "★ Standard (65% Secondary + 35% Exams)",
                "= Equal Weight (50% Secondary + 50% Exams)",
                "→ Exam-Heavy (40% Secondary + 60% Exams)",
                "← Secondary-Heavy (70% Secondary + 30% Exams)",
                "✐ Custom (Set your own)"
            ],
            key="weight_calculation_option"
        )
        
        weights = None
        
        if "Standard" in weight_option:
            weights = {'secondary': 0.65, 'exam': 0.35}
            st.info("✓ Most common formula (65:35)")
        
        elif "Equal Weight" in weight_option:
            weights = {'secondary': 0.50, 'exam': 0.50}
            st.info("✓ Balanced approach (50:50)")
        
        elif "Exam-Heavy" in weight_option:
            weights = {'secondary': 0.40, 'exam': 0.60}
            st.info("✓ Favors strong exam performance (40:60)")
        
        elif "Secondary-Heavy" in weight_option:
            weights = {'secondary': 0.70, 'exam': 0.30}
            st.info("✓ Rewards consistent school grades (70:30)")
        
        else:
            st.write("**Set custom weights** (must add to 100%):")
            col1, col2 = st.columns(2)
            
            with col1:
                secondary_pct = st.slider(
                    "Secondary School %",
                    min_value=0,
                    max_value=100,
                    value=65,
                    step=5,
                    key="custom_secondary_slider"
                )
            
            with col2:
                exam_pct = 100 - secondary_pct
                st.metric("Exam %", f"{exam_pct}%")
            
            weights = {'secondary': secondary_pct / 100, 'exam': exam_pct / 100}
            st.info(f"✓ Using {secondary_pct}:{exam_pct} split")
    
    
    # calculate button
    if st.button("÷ Calculate My Final Grade", width='stretch', type="primary", key="btn_calculate_final_grade"):
        st.session_state.grades_calculation_weights = weights
        
        # calculating the final grade
        final_grade = calculate_admission_average(grades_data, weights)
        st.session_state.student_final_grade = final_grade
        
        # saving to reports
        if "username" in st.session_state and st.session_state.username:
            report_content = generate_simple_grade_report(grades_data, final_grade, weights)
            
            try:
                save_report(
                    user_id=st.session_state.username,
                    report_type="grades",
                    title=f"Grades - CIF {final_grade:.1f}/20 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content=json.dumps({
                        "student_grades_data": st.session_state.student_grades_data,
                        "final_cif": float(final_grade),
                        "weights_used": weights,
                        "summary": report_content
                        }),
                    cv_data=None
                    )
                st.session_state.final_grade_calculated = True
                st.rerun()
            except Exception as e:
                st.error(f"⚠︎ Could not save: {e}")

def show_final_results():
    """Showing final grade and offer course comparison options"""
    
    # CHECK IF INTERNATIONAL STUDENT - DIFFERENT FLOW
    if st.session_state.get("student_type") == "international":
        show_international_final_results()
        return
    
    # REST OF CODE FOR PORTUGUESE STUDENTS
    raw_final_grade = st.session_state.student_final_grade
    # normalizing to 0–20 scale if needed
    final_grade_20 = raw_final_grade / 10.0 if raw_final_grade > 20 else raw_final_grade
    
    weights = st.session_state.grades_calculation_weights
    
    st.success("✓ Your final grade has been calculated and saved!")
    
    st.markdown("𖥠 Your Admission Average")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric(
            "✪ Final Grade", 
            f"{final_grade_20:.2f}/20",
            help=f"Calculated using {int(weights['secondary']*100)}:{int(weights['exam']*100)} formula"
        )
    
    with col2:
        st.write("**ℹ Formula:**")
        st.write(f"{int(weights['secondary']*100)}% Secondary")
        st.write(f"{int(weights['exam']*100)}% Exams")
    
    
    # 3 options for comparing against courses
    st.subheader("Compare Against Courses")
    st.write("Choose how you want to see your chances:")
    
    tab1, tab2, tab3 = st.tabs(["✍︎ Manual Entry", "☰ From Degree Picker", "𖠿 From Saved Universities"])
    
    # tab 1 for manual course name
    with tab1:
        st.write("**Enter a course name manually:**")
        manual_course = st.text_input(
            "Course name:",
            placeholder="e.g., Medicina, Engenharia Informática",
            key="manual_course_input"
        )
        
        if manual_course and st.button("Check This Course", key="check_manual", width='stretch'):
            # check_course_grade_range expects CIF 0–200 scale, so we are passing raw_final_grade
            check_course_grade_range(manual_course, raw_final_grade)
    
    # tab 2 for degree picker results
    with tab2:
        st.write("**Use degrees from your Degree Picker results:**")
        
        if "username" in st.session_state and st.session_state.username:
            try:
                degree_reports = load_reports(st.session_state.username, report_type="degree")
                
                if degree_reports:
                    latest_degree_report = sorted(
                        degree_reports, 
                        key=lambda x: x.get("timestamp", ""), 
                        reverse=True
                    )[0]
                    
                    content = latest_degree_report.get("content", "")
                    
                    degree_pattern = r'###\s*\d+\.\s*([^(]+?)\s*\('
                    degree_matches = re.findall(degree_pattern, content)
                    
                    if degree_matches:
                        degree_options = [d.strip() for d in degree_matches if len(d.strip()) > 3]
                        
                        if degree_options:
                            st.success(f"✓ Found {len(degree_options)} degrees from your latest Degree Picker report")
                            
                            selected_degree = st.selectbox(
                                "Select a degree:",
                                degree_options,
                                key="degree_picker_select"
                            )
                            
                            if st.button("⟡Check This Degree", key="check_degree", width='stretch'):
                                check_course_grade_range(selected_degree, raw_final_grade)
                        else:
                            st.info("⚠︎ Could not extract degrees from your report.")
                            show_degree_picker_button()
                    else:
                        st.info("⚠︎ No degree patterns found in your report.")
                        show_degree_picker_button()
                else:
                    st.info("⚠︎ No Degree Picker results found. Complete the Degree Picker first!")
                    show_degree_picker_button()
                    
            except Exception as e:
                st.error(f"⚠︎ Error loading Degree Picker results: {e}")
                show_degree_picker_button()
        else:
            st.warning("⚠︎ Please log in to see your Degree Picker results!")
    
    # tab 3 for saved universities
    with tab3:
        st.write("**Use universities you've saved:**")
        
        if "username" in st.session_state and st.session_state.username:
            try:
                # loading only university reports
                uni_reports = load_reports(st.session_state.username, report_type="university")
                
                if uni_reports:
                    st.success(f"✓ Found {len(uni_reports)} saved universities")
                    
                    saved_universities_data = []
                    
                    for report in uni_reports[:20]:
                        content = report.get("content", "")
                        title = report.get("title", "")
                        
                        # program + uni from title: "University - [Program] - [Uni Name] - Date"
                        program_name = "Unknown"
                        uni_name = "Unknown"
                        if title.startswith("University - "):
                            parts = title.split(" - ")
                            if len(parts) >= 3:
                                program_name = parts[1].strip()
                                uni_name = parts[2].strip()
                        
                        # 1) trying to get the last admitted grade from "Quick Info"
                        grade = None
                        
                        patterns = [
                            r"Last Admitted Grade:\s*\*\*([0-9]+(?:\.[0-9]+)?)\/20\*\*",
                            r"Last Admitted Grade:\s*([0-9]+(?:\.[0-9]+)?)\/20",
                            r"Last admitted grade:\s*\*\*([0-9]+(?:\.[0-9]+)?)\/20\*\*",
                            r"Last admitted grade:\s*([0-9]+(?:\.[0-9]+)?)\/20",
                        ]
                        
                        for pat in patterns:
                            m = re.search(pat, content)
                            if m:
                                raw = float(m.group(1))
                                # If it's 0–200 scale convert to 0–20
                                grade = raw / 10.0 if raw > 20 else raw
                                break
                        
                        # 2) fallback "Required Grade" section if present
                        if grade is None:
                            req_patterns = [
                                r"\*\*Required Grade:\*\*\s*([0-9]+(?:\.[0-9]+)?)\/20",
                                r"\*\*Required Grade:\*\*\s*([0-9]+(?:\.[0-9]+)?)",
                            ]
                            for pat in req_patterns:
                                m = re.search(pat, content)
                                if m:
                                    raw = float(m.group(1))
                                    grade = raw / 10.0 if raw > 20 else raw
                                    break
                        
                        # skipping if no grade found
                        if grade is None:
                            continue
                        
                        saved_universities_data.append(
                            {
                                "program": program_name,
                                "university": uni_name,
                                "required_grade": grade,  # normalized 0–20
                                "content": content[:300],
                            }
                        )
                    
                    if saved_universities_data:
                        st.write(f"**Comparing your grade ({final_grade_20:.2f}/20) against your saved universities:**")
                        
                        # sorting by required grade (ascending)
                        saved_universities_data.sort(key=lambda x: x["required_grade"])
                        
                        # categorising
                        safe = []
                        possible = []
                        reach = []
                        
                        for uni_data in saved_universities_data:
                            req = uni_data["required_grade"]
                            diff = final_grade_20 - req
                            
                            if diff >= 1.0:
                                safe.append((uni_data, diff))
                            elif diff >= -1.0:
                                possible.append((uni_data, diff))
                            else:
                                reach.append((uni_data, diff))
                        
                        # safe
                        if safe:
                            st.subheader(f"🟢 Safe Choices ({len(safe)})")
                            st.caption("Your grade is comfortably above the requirement.")
                            for uni_data, diff in safe:
                                with st.expander(f"✓ {uni_data['university']} - {uni_data['program']}", expanded=False):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Your Grade", f"{final_grade_20:.2f}/20")
                                    with col2:
                                        st.metric("Required", f"{uni_data['required_grade']:.2f}/20")
                                    with col3:
                                        label = f"{diff:+.2f}"
                                        st.metric("Difference", label, delta=label)
                                    st.success(f"You exceed the requirement by **{diff:.2f} points**.")

                        # target
                        if possible:
                            st.subheader(f"🟡 Target Choices ({len(possible)})")
                            st.caption("Your grade is around the requirement (±1 point).")
                            for uni_data, diff in possible:
                                with st.expander(f"⚖ {uni_data['university']} - {uni_data['program']}", expanded=False):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Your Grade", f"{final_grade_20:.2f}/20")
                                    with col2:
                                        st.metric("Required", f"{uni_data['required_grade']:.2f}/20")
                                    with col3:
                                        label = f"{diff:+.2f}"
                                        st.metric("Difference", label, delta=label)
                                    if diff >= 0:
                                        st.info(f"You meet the requirement (+{diff:.2f} points).")
                                    else:
                                        st.warning(f"You are slightly below by {abs(diff):.2f} points – still possible.")
                        
                        # reach
                        if reach:
                            st.subheader(f"🔴 Reach Choices ({len(reach)})")
                            st.caption("Your grade is more than 1 point below the requirement.")
                            for uni_data, diff in reach:
                                with st.expander(f"⚐ {uni_data['university']} - {uni_data['program']}", expanded=False):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Your Grade", f"{final_grade_20:.2f}/20")
                                    with col2:
                                        st.metric("Required", f"{uni_data['required_grade']:.2f}/20")
                                    with col3:
                                        label = f"{diff:+.2f}"
                                        st.metric("Gap", label, delta=label)
                                    st.error(f"Need to improve by **{abs(diff):.2f} points** to reach this program. Good luck!")

                    else:
                        st.warning("⚠︎ Could not extract grade requirements from your saved universities.")
                        st.info("Try saving universities again from University Finder so they include grade info.")
                else:
                    st.info("ⓘ No saved universities found. Use University Finder first!")
                    show_university_finder_button()
                    
            except Exception as e:
                st.error(f"Error loading saved universities: {e}")
                show_university_finder_button()
        else:
            st.warning("Please log in to see your saved universities!")
    
    st.markdown("---")
    st.subheader("What's Next?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("𖠿 Find Universities", width='stretch', type="primary", key="ga_to_uni"):
            st.session_state.redirect_to = "University Finder"
            st.rerun()

    with col2:
        if st.button("← Explore Degrees", width='stretch', key="ga_to_degree"):
            st.session_state.redirect_to = "Degree Picker"
            st.rerun()

    with col3:
        if st.button("↻ Recalculate", width='stretch', key="ga_to_recalc"):
            reset_grades_analysis()
            st.rerun()


def show_international_final_results():
    """Show results for international students without grade calculation"""
    
    grades_data = st.session_state.student_grades_data
    
    st.success("✓ Your grades have been saved!")
    
    st.subheader("☰ Your Grades Summary")
    
    subjects = grades_data.get("subjects", [])
    
    if subjects:
        st.write(f"**Total Subjects:** {len(subjects)}")
        st.write(f"**Country:** {grades_data.get('country', 'International')}")
        st.write(f"**Grade Scale:** {grades_data.get('grade_scale', 'Various')}")
        
        with st.expander("View All Subjects"):
            for subj in subjects:
                st.write(f"- {subj['name']}: {subj['grade']} ({subj.get('year', 'N/A')})")
    
    st.markdown("---")
    
    # AI OVERVIEW BUTTON
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⟡ Get AI Overview", width='stretch', type="primary", key="btn_ai_overview_final"):
            with st.spinner("Analyzing your grades..."):
                overview = generate_international_grades_overview(grades_data)
                if overview:
                    st.markdown("---")
                    st.subheader("☰ Your Academic Profile")
                    st.markdown(overview)
    
    with col2:
        if st.button("↻ Add More Grades", width='stretch', key="btn_add_more_final"):
            reset_grades_analysis()
            st.rerun()
    
    st.markdown("---")
    st.subheader("What's Next?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("𖠿 Find Universities", width='stretch', type='primary', key="intl_to_uni"):
            st.session_state.redirect_to = "University Finder"
            st.rerun()
    
    with col2:
        if st.button("← Explore Degrees", width='stretch', key="intl_to_degree"):
            st.session_state.redirect_to = "Degree Picker"
            st.rerun()


def show_degree_picker_button():
    """Helper to show Degree Picker redirect button"""
    if st.button("Go to Degree Picker", width='stretch', key="btn_goto_dp_from_tab"):
        st.session_state.redirect_to = "Degree Picker"
        st.rerun()


def show_university_finder_button():
    """Helper to show University Finder redirect button"""
    if st.button("Go to University Finder", width='stretch', key="btn_goto_uf_from_tab"):
        st.session_state.redirect_to = "University Finder"
        st.rerun()


def check_course_grade_range(course_name, student_grade):
    """Check grade range for a specific course - NO UNIVERSITY LIST"""
    
    
    with st.spinner(f"Searching DGES database for {course_name}!"):
        dges_results = fetch_dges_data(course_name)
    
    if not dges_results:
        st.error(f"⃠ No programs found for '{course_name}'. Try a different name.")
        return
    
    # using only positive grades, so above 0
    valid_grades = [
        p["last_entry_grade"] 
        for p in dges_results 
        if p.get("last_entry_grade") and p["last_entry_grade"] > 0
    ]
    
    if not valid_grades:
        st.error("⃠ No valid entry grades found for this course.")
        st.info("The DGES data for these programs does not include last entry grades.")
        return
    
    min_grade = min(valid_grades)
    max_grade = max(valid_grades)
    avg_grade = sum(valid_grades) / len(valid_grades)
    
    st.success(f"✓ Found {len(dges_results)} programs for **{course_name}**")
    
    # showing grade comparison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Your Grade", f"{student_grade:.2f}")
    
    with col2:
        st.metric("Lowest Entry", f"{min_grade:.0f}")
        if student_grade >= min_grade:
            st.success("✓ Above minimum")
        else:
            st.error(f"✗ Need +{min_grade - student_grade:.2f}")
    
    with col3:
        st.metric("Highest Entry", f"{max_grade:.0f}")
        if student_grade >= max_grade:
            st.success("✓ Competitive everywhere")
        elif student_grade >= avg_grade:
            st.info("~ Competitive for most")
        else:
            st.warning("⚠ Below average")
    
    # visual indicators
    st.markdown("### Grade Range Visualization")
    
    if student_grade < min_grade:
        status = "🔴 Below minimum - Need to improve"
        position = 0
    elif student_grade >= max_grade:
        status = "🟢 Excellent - Competitive everywhere!"
        position = 100
    else:
        position = ((student_grade - min_grade) / (max_grade - min_grade)) * 100
        if position >= 75:
            status = "🟢 Strong - Good chances at most programs"
        elif position >= 50:
            status = "🟡 Moderate - Competitive for many programs"
        else:
            status = "🟠 Borderline - Limited options"
    
    st.progress(position / 100)
    st.write(f"**Status:** {status}")
    


def calculate_admission_average(grades_data, weights):
    """Calculate Portuguese admission average (CIF)"""
    
    grades = grades_data.get("grades", {})
    current_year = grades_data.get("current_year", "12th Grade (Completed)")
    
    # calculating secondary average
    all_grades = []
    for year in ["10th", "11th", "12th"]:
        year_grades = grades.get(year, {})
        all_grades.extend([g for g in year_grades.values() if g > 0])
    
    secondary_avg = sum(all_grades) / len(all_grades) if all_grades else 0
    
    # getting exam grades (scale 0-200)
    exams = grades.get("exams", {})
    exam_avg = sum(exams.values()) / len(exams) if exams else 0
    
    # converting secondary to 200 scale
    secondary_200 = secondary_avg * 10
    
    # special case when 10th graders haven't taken exams yet
    if "10th" in current_year:
        # 100% secondary school grades
        cif = secondary_200
    # 11th graders might have partial exams or predictions
    elif "11th" in current_year:
        if exam_avg > 0:
            # using weights if they have exam scores/predictions
            cif = (secondary_200 * weights['secondary']) + (exam_avg * weights['exam'])
        else:
            # no exams yet, using 100% secondary
            cif = secondary_200
    # 12th graders should have exams
    else:
        if exam_avg > 0:
            # applying weights normally
            cif = (secondary_200 * weights['secondary']) + (exam_avg * weights['exam'])
        else:
            # fallback to secondary only if no exams recorded
            cif = secondary_200
    
    return cif


def generate_simple_grade_report(grades_data, final_grade, weights):
    """Generate simple report for saving"""
    
    grades = grades_data.get("grades", {})
    current_year = grades_data.get("current_year", "12th Grade (Completed)")
    
    # determining calculation type
    if weights['exam'] == 0:
        calc_method = "100% Secondary School Grades (No exams yet)"
    else:
        calc_method = f"{int(weights['secondary']*100)}% Secondary + {int(weights['exam']*100)}% Exams"
    
    report = f"""# Grades Analysis Report

## Final Admission Average
**CIF Score:** {final_grade:.2f}

**Current Year:** {current_year}  
**Calculation Method:** {calc_method}

## Grade Breakdown

### Secondary School Grades (10th-12th)
"""
    
    for year in ["10th", "11th", "12th"]:
        year_grades = grades.get(year, {})
        if year_grades:
            valid_grades = [g for g in year_grades.values() if g > 0]
            if valid_grades:
                avg = sum(valid_grades) / len(valid_grades)
                report += f"\n**{year} Grade:** {avg:.2f}\n"
                for subject, grade in year_grades.items():
                    if grade > 0:
                        report += f"  - {subject}: {grade}\n"
            else:
                report += f"\n**{year} Grade:** No grades entered yet\n"
    
    report += "\n### National Exams\n"
    exams = grades.get("exams", {})
    if exams and any(score > 0 for score in exams.values()):
        for exam, grade in exams.items():
            if grade > 0:
                report += f"- {exam}: {grade}\n"
    else:
        if "10th" in current_year:
            report += "*No exams - 10th grade student*\n"
        else:
            report += "*No exams recorded yet*\n"
    
    report += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    
    return report

def fetch_dges_data(course_name: str):
    """Fetch DGES data for a specific course"""
    if "universities_df" not in st.session_state:
        st.error("DGES data not loaded!")
        return []

    df = st.session_state["universities_df"]
    
    normalized = normalize_text(course_name)
    df = df.copy()
    df["course_name_normalized"] = df["course_name"].apply(normalize_text)
    
    mask = df["course_name_normalized"].str.contains(normalized, case=False, na=False)
    results = df[mask].copy()
    
    if results.empty:
        return []
    
    programs = []
    for _, row in results.iterrows():
        programs.append({
            "university": row["institution_name"],
            "course": row["course_name"],
            "location": row.get("region", "Other"),
            "last_entry_grade": float(row["last_grade"]) if "last_grade" in row and pd.notna(row["last_grade"]) else 0.0,
        })
    
    return programs


def reset_grades_analysis():
    """Reset all grades analysis state"""
    st.session_state.grades_input_method = None
    st.session_state.student_grades_data = None
    st.session_state.grades_calculation_weights = None
    st.session_state.final_grade_calculated = False
    if "temp_grades" in st.session_state:
        del st.session_state.temp_grades
    if "student_final_grade" in st.session_state:
        del st.session_state.student_final_grade

def render_manual_grades_input():
    """Manual grades entry with smart year-based collection"""
    
    st.subheader("✍︎ Manual Grades Entry")
    

    
    
    st.subheader("Step 1: Select Your Track")
    track = st.selectbox(
        "What track are you in?",
        ["Ciências e Tecnologias", "Ciências Socioeconómicas", "Línguas e Humanidades", "Artes Visuais"],
        key="track_select"
    )
    
    if "last_selected_track" not in st.session_state:
        st.session_state.last_selected_track = track
    
    if st.session_state.last_selected_track != track:
        st.session_state.last_selected_track = track
        if "temp_grades" in st.session_state:
            st.session_state.temp_grades = {
                "10th": {},
                "11th": {},
                "12th": {},
                "exams": {}
            }
        if "custom_subjects" in st.session_state:
            st.session_state.custom_subjects = {
                "10th": [],
                "11th": [],
                "12th": []
            }
        st.rerun()
    
    
    st.subheader("Step 2: Select Your Year")
    current_year = st.selectbox(
        "What year are you currently in?",
        ["10th Grade", "11th Grade", "12th Grade (In Progress)", "12th Grade (Completed)"],
        key="current_year_select"
    )
    
    
    if "temp_grades" not in st.session_state:
        st.session_state.temp_grades = {
            "10th": {},
            "11th": {},
            "12th": {},
            "exams": {}
        }
    
    if "custom_subjects" not in st.session_state:
        st.session_state.custom_subjects = {
            "10th": [],
            "11th": [],
            "12th": []
        }
    
    ALL_SUBJECTS = [
        "Português", "Inglês", "Francês", "Espanhol", "Alemão",
        "Matemática", "Matemática A", "Matemática B",
        "Físico-Química", "Física e Química A",
        "Biologia e Geologia", "Biologia", "Geologia",
        "História", "História A", "História B",
        "Geografia", "Geografia A", "Geografia B",
        "Filosofia", "Psicologia",
        "Economia", "Economia A",
        "Educação Física", "Educação Visual",
        "Desenho A", "Geometria Descritiva A",
        "Literatura Portuguesa", "História da Cultura e das Artes",
        "Sociologia", "Antropologia",
        "Aplicações Informáticas", "TIC"
    ]
    
    SUBJECTS_10_BASE = [
        "Português", "Inglês", "Educação Física"
    ]
    
    SUBJECTS_11_12_BASE = [
        "Português", "Inglês", "Filosofia", "Educação Física"
    ]
    
    track_subjects_map = {
        "Ciências e Tecnologias": ["Matemática A", "Física e Química A", "Biologia e Geologia"],
        "Ciências Socioeconómicas": ["Matemática A", "Economia A", "Geografia A"],
        "Línguas e Humanidades": ["História A", "Geografia A", "Literatura Portuguesa"],
        "Artes Visuais": ["Desenho A", "História da Cultura e das Artes", "Geometria Descritiva A"]
    }
    
    track_subjects = track_subjects_map.get(track, [])
    
    years_to_collect = []
    if "10th" in current_year:
        years_to_collect = ["10th"]
    elif "11th" in current_year:
        years_to_collect = ["10th", "11th"]
    else:
        years_to_collect = ["10th", "11th", "12th"]
    
    # st.info(f"Track: **{track}** | Main subjects for this track: {', '.join(track_subjects)}")
    
    for year_idx, year in enumerate(years_to_collect):
        st.subheader(f"Step {3 + year_idx}: {year} Grade Subjects")
        
        if year == "10th":
            base_subjects = SUBJECTS_10_BASE + track_subjects
        else:
            base_subjects = SUBJECTS_11_12_BASE + track_subjects
        
        all_subjects_for_year = base_subjects + st.session_state.custom_subjects[year]
        
        seen = set()
        all_subjects_for_year = [x for x in all_subjects_for_year if not (x in seen or seen.add(x))]
        
        st.write(f"**⛶ Core subjects for {year}:**")
        
        for i in range(0, len(all_subjects_for_year), 2):
            cols = st.columns(2)
            
            for col_idx, col in enumerate(cols):
                if i + col_idx < len(all_subjects_for_year):
                    subject = all_subjects_for_year[i + col_idx]
                    
                    with col:
                        is_custom = subject in st.session_state.custom_subjects[year]
                        
                        col_input, col_delete = st.columns([5, 1])
                        
                        with col_input:
                            grade = st.number_input(
                                subject,
                                min_value=0,
                                max_value=20,
                                value=st.session_state.temp_grades[year].get(subject, 0),
                                step=1,
                                key=f"{track}_{year}_{subject}"
                            )
                            st.session_state.temp_grades[year][subject] = grade
                        
                        with col_delete:
                            if is_custom:
                                st.write("")
                                if st.button("🗑️", key=f"del_{track}_{year}_{subject}"):
                                    st.session_state.custom_subjects[year].remove(subject)
                                    if subject in st.session_state.temp_grades[year]:
                                        del st.session_state.temp_grades[year][subject]
                                    st.rerun()
        
        st.write(f"**Add extra subjects for {year}:**")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            available_subjects = [s for s in ALL_SUBJECTS if s not in all_subjects_for_year]
            
            selected_subject = st.selectbox(
                f"Select from list",
                [""] + available_subjects,
                key=f"dropdown_{year}",
                label_visibility="collapsed"
            )
        
        with col2:
            custom_subject_name = st.text_input(
                f"Or type subject name",
                key=f"custom_text_{year}",
                placeholder="Type subject name...",
                label_visibility="collapsed"
            )
        
        with col3:
            st.write("")
            if st.button(f"+ Add", key=f"add_{year}", width='stretch'):
                new_subject = None
                
                if selected_subject and selected_subject != "":
                    new_subject = selected_subject
                elif custom_subject_name and custom_subject_name.strip() != "":
                    new_subject = custom_subject_name.strip()
                
                if new_subject and new_subject not in all_subjects_for_year:
                    st.session_state.custom_subjects[year].append(new_subject)
                    st.rerun()
                elif new_subject in all_subjects_for_year:
                    st.error(f"{new_subject} is already in your list!")
                else:
                    st.warning("Please select or type a subject name first!")
        
    
    if "11th" in current_year or "12th" in current_year:
        st.subheader("National Exams")
        
        exam_status = "Completed" if current_year == "12th Grade (Completed)" else "Not Completed"
        
        if exam_status == "Not Completed":
            st.info("ⓘ Add your exam grades or grade predictions below!")
        
        COMMON_EXAMS = {
            "Português (639)": "639",
            "Matemática A (635)": "635",
            "Física e Química A (715)": "715",
            "Biologia e Geologia (702)": "702",
            "História A (623)": "623",
            "Geografia A (719)": "719",
            "Economia A (712)": "712",
            "Inglês (550)": "550",
            "Filosofia (714)": "714",
            "Geometria Descritiva A (708)": "708",
            "Desenho A (706)": "706"
        }
        
        selected_exams = st.multiselect(
            "Which exams have you taken / will you take?",
            list(COMMON_EXAMS.keys()),
            key="exams_multiselect"
        )
        
        exam_cols = st.columns(2)
        for i, exam in enumerate(selected_exams):
            with exam_cols[i % 2]:
                if exam_status == "Completed":
                    grade = st.number_input(
                        f"Grade for {exam}",
                        min_value=0,
                        max_value=200,
                        value=st.session_state.temp_grades["exams"].get(exam, 0),
                        step=1,
                        key=f"exam_{exam}_completed"
                    )
                    st.session_state.temp_grades["exams"][exam] = grade
                else:
                    predicted = st.number_input(
                        f"Predicted/Target grade for {exam}",
                        min_value=0,
                        max_value=200,
                        value=st.session_state.temp_grades["exams"].get(exam, 100),
                        step=5,
                        key=f"exam_{exam}_predicted",
                        help="What grade do you think you'll get? Or leave as estimate."
                    )
                    st.session_state.temp_grades["exams"][exam] = predicted

    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back", width='stretch', key="btn_back_from_manual_grades"):
            st.session_state.grades_input_method = None
            st.rerun()
    
    with col2:
        if st.button("Calculate My Admission Average →", width='stretch', type="primary", key="btn_submit_manual_grades"):
            has_grades = any(
                st.session_state.temp_grades[year] 
                for year in years_to_collect
            )
            
            if has_grades:
                st.session_state.student_grades_data = {
                    "current_year": current_year,
                    "track": track,
                    "grades": st.session_state.temp_grades,
                    "input_method": "manual",
                }
                st.session_state.student_grades_data = {
                    "inputmethod": "manual",
                    "grades": st.session_state.temp_grades,
                }
                st.rerun()
            else:
                st.error("⚠︎ Please fill in at least some grades before continuing!")


