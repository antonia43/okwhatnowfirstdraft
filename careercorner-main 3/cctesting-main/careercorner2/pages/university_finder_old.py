import re
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import unicodedata
from utils.database import (
    init_database,
    save_university,
    get_saved_universities,
    remove_saved_university,
    is_university_saved,
    get_saved_count,
    load_reports,
    clear_all_saved,
    delete_report,
    save_report
)
from services.langfuse_helper import get_user_id
from datetime import datetime


# Initialize database on module load
init_database()

def get_student_admission_average():
    """Load CIF from grades reports (JSON format)"""
    user_id = get_user_id()
    
    try:

        import json
        grades_reports = load_reports(user_id, "grades")
        
        if grades_reports:
            latest_report = grades_reports[0]
            report_data = json.loads(latest_report['content'])
            
            if "final_cif" in report_data:
                return report_data["final_cif"]
            
            elif "student_grades_data" in report_data:
                gradesdata = report_data["student_grades_data"]
                if gradesdata.get("inputmethod") == "manual":
                    grades = gradesdata.get("grades", {})
                    all_grades = []
                    for year in ["10th", "11th", "12th"]:
                        year_grades = grades.get(year, {})
                        all_grades.extend([g for g in year_grades.values() if g > 0])
                    if all_grades:
                        secondary_avg = sum(all_grades) / len(all_grades)
                        exams = grades.get("exams", {})
                        exam_avg = sum(exams.values()) / len(exams) if exams else 0
                        if exam_avg > 0:
                            secondary_200 = secondary_avg * 10
                            cif = (secondary_200 * 0.65) + (exam_avg * 0.35)
                            return cif / 10
                        else:
                            return secondary_avg
                elif gradesdata.get("inputmethod") in ["manualinternational", "fileinternational"]:
                    subjects = gradesdata.get("subjects", [])
                    if subjects:
                        grades_list = [float(s.get("grade", 0)) for s in subjects if s.get("grade")]
                        if grades_list:
                            return min(sum(grades_list) / len(grades_list), 20)
        
        # Fallback
        if "student_grades_data" in st.session_state:
            gradesdata = st.session_state["student_grades_data"]
            if gradesdata.get("inputmethod") == "manual":
                grades = gradesdata.get("grades", {})
                all_grades = []
                for year in ["10th", "11th", "12th"]:
                    year_grades = grades.get(year, {})
                    all_grades.extend([g for g in year_grades.values() if g > 0])
                if all_grades:
                    secondary_avg = sum(all_grades) / len(all_grades)
                    exams = grades.get("exams", {})
                    exam_avg = sum(exams.values()) / len(exams) if exams else 0
                    if exam_avg > 0:
                        secondary_200 = secondary_avg * 10
                        cif = (secondary_200 * 0.65) + (exam_avg * 0.35)
                        return cif / 10
                    else:
                        return secondary_avg
            elif gradesdata.get("inputmethod") in ["manualinternational", "fileinternational"]:
                subjects = gradesdata.get("subjects", [])
                if subjects:
                    grades_list = [float(s.get("grade", 0)) for s in subjects if s.get("grade")]
                    if grades_list:
                        return min(sum(grades_list) / len(grades_list), 20)
        
        return None
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Grade parse error: {e}")
        return None


def render_university_finder():
    """
    Finding universities offering the student's chosen degree
    Shows on map with filters using real DGES data
    """
    st.header("𖤣 University Finder")
    
    user_id = get_user_id()

    # one time gate flag
    if "university_pt_gate_done" not in st.session_state:
        st.session_state.university_pt_gate_done = False

    # this is a gate to confirm user is applying in Portugal before showing the page
    if not st.session_state.university_pt_gate_done:
        st.info(
            """
            This tool uses **DGES data for Portuguese universities**. It only works if you are:  

            ✦ Planning to study in **Portugal**    
            ✦ Comparing **Portuguese** degrees and entry grades
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🇵🇹 Yes, I'm applying in Portugal!",
                width='stretch',
                type="primary",
                key="uf_pt_yes",
            ):
                st.session_state.university_pt_gate_done = True
                st.rerun()
        with col2:
            if st.button(
                "🌍 I'm not applying in Portugal!",
                width='stretch',
                key="uf_pt_no",
            ):
                st.warning(
                    "For now, University Finder only supports Portuguese universities. "
                    "You can still use the Degree Picker and Grades Analysis."
                )
        return
    
    # loading degree reports from our database

    degree_reports = load_reports(user_id, "degree")
    has_degree_reports = bool(degree_reports)

    if not has_degree_reports:
        st.info(
            "⚠︎ Complete the Degree Picker first to get personalized degree ideas, "
            "or search universities directly below."
        )
        if st.button("Go to Degree Picker", width='stretch'):
            st.session_state.redirect_to = "Degree Picker"
            st.rerun()
        st.markdown("---")

    # saved universities
    saved_count = get_saved_count(user_id)
    if saved_count > 0:
        with st.expander(f"𖠿 Your Saved Universities ({saved_count})", expanded=False):
            saved_universities = get_saved_universities(user_id)
            for uni in saved_universities:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(
                        f"**{uni['name']}** - {uni['program_name']} "
                        f"({uni['average_grade_required']})"
                    )
                with col2:
                    if st.button(
                        "🗑️",
                        key=f"remove_{uni['name']}_{uni['program_name']}",
                        help="Remove",
                    ):
                        if remove_saved_university(user_id, uni["name"], uni["program_name"]):
                            st.success("Removed!")
                            st.rerun()

            if st.button("🗑️ Clear All Saved", type="secondary"):
                if clear_all_saved(user_id):

                    uni_reports = load_reports(user_id, "university")
                    for report in uni_reports:
                        delete_report(report['id'])
                    st.success("☑ Cleared saved unis + reports!")
                    st.rerun()


        st.markdown("---")

    st.subheader("What degree are you looking for?")
    use_report = False
    degree = ""

    # option 1 is using saved degree report
    if has_degree_reports:
        use_report = st.checkbox(
            "Use degree from My Reports",
            value=True,
            key="uf_use_report",
        )

    if use_report and has_degree_reports:
        # selecting which report to use
        report_titles = [r["title"] for r in degree_reports]
        selected_report_title = st.selectbox(
            "Select your degree report:",
            report_titles,
            key="uf_report_selector",
        )
        
        # extracting degrees from selected report
        # pattern ### 1. Degree Name (fit%)
        pattern = r'###\s*\d+\.\s*([^(]+?)\s*\('
        selected_report = next(r for r in degree_reports if r["title"] == selected_report_title)
        content = selected_report.get("content", "")
        degree_matches = re.findall(pattern, content)
        
        if degree_matches:
            clean_degrees = [d.strip() for d in degree_matches if len(d.strip()) > 3]
            
            if clean_degrees:
                degree = st.selectbox(
                    "Pick a degree from your report:",
                    clean_degrees,
                    key="uf_report_degree_select",
                )
            else:
                st.warning("Could not extract degrees. Showing report content - copy/paste a degree name below.")
                with st.expander("View Report Content"):
                    st.markdown(content)
                use_report = False
        else:
            st.warning("Could not auto-extract degrees. Copy a degree name from your report:")
            with st.expander("View Your Report", expanded=True):
                st.markdown(content)
            use_report = False

    if not use_report:
        # manual input
        if "last_degree_input" not in st.session_state:
            st.session_state.last_degree_input = ""
        if "last_degree_select" not in st.session_state:
            st.session_state.last_degree_select = ""

        if "universities_df" in st.session_state and not st.session_state["universities_df"].empty:
            common_degrees = [
                "Informática",
                "Engenharia",
                "Gestão",
                "Enfermagem",
                "Psicologia",
                "Medicina",
                "Direito",
                "Ciências",
                "Comunicação",
                "Design",
                "Arquitetura",
                "Turismo",
                "Educação",
                "Desporto",
                "Biotecnologia",
            ]
        else:
            common_degrees = [
                "Informática",
                "Engenharia",
                "Gestão",
                "Psicologia",
                "Medicina",
                "Direito",
            ]

        col1, col2 = st.columns([2, 1])
        with col1:
            degree_input = st.text_input(
                "Type your degree (e.g., 'Informática', 'Engenharia Civil', 'Medicina'):",
                placeholder="Start typing...",
                value=st.session_state.last_degree_input,
                key="degree_text_input",
            )
        with col2:
            dropdown_index = 0
            if st.session_state.last_degree_select in common_degrees:
                dropdown_index = common_degrees.index(st.session_state.last_degree_select) + 1

            degree_select = st.selectbox(
                "Or pick from popular degrees:",
                [""] + common_degrees,
                index=dropdown_index,
                key="degree_quick_select",
            )

        # sync logic
        if degree_select and degree_select != st.session_state.last_degree_select:
            st.session_state.last_degree_select = degree_select
            st.session_state.last_degree_input = ""
            degree = degree_select
            st.rerun()
        elif degree_input != st.session_state.last_degree_input:
            st.session_state.last_degree_input = degree_input
            st.session_state.last_degree_select = ""
            degree = degree_input
            st.rerun()
        else:
            degree = degree_select if degree_select else degree_input

    if not degree:
        st.info("ⓘ Enter or select a degree to start searching")
        return

    st.success(f"Searching for universities offering **{degree}**")
    st.markdown("---")


    # filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        location = st.selectbox(
            "Region:",
            [
                "All of Portugal",
                "Lisbon",
                "Porto",
                "Coimbra",
                "Braga",
                "Faro",
                "Aveiro",
                "Leiria",
                "Évora",
                "Other",
            ],
        )
    with col2:
        uni_type = st.multiselect(
            "University Type:",
            ["Public", "Private", "Polytechnic"],
            default=["Public", "Polytechnic"],
        )
    with col3:
        ranking = st.select_slider(
            "Ranking:",
            options=["Any", "Top 10", "Top 20", "Top 50"],
            value="Any",
        )

    show_grade_filter = st.session_state.get("uf_grade_filter", True)
    grade_margin = st.session_state.get("uf_grade_margin", 0.5)

    if use_report:
        search_universities(degree, location, uni_type, ranking, show_grade_filter, grade_margin)
    else:
        if st.button("Search Universities", width='stretch', type="primary"):
            search_universities(degree, location, uni_type, ranking, show_grade_filter, grade_margin)
            st.rerun()       
    if "university_results" in st.session_state and st.session_state.university_results:
        render_university_results()


def normalize_text(text):
    """Removing accents and normalizing the text for better matching"""
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower()

def search_universities(degree, location, uni_type, ranking, show_grade_filter=True, grade_margin=0.5):
    """Searching for universities using local DGES CSV data"""

    if "universities_df" not in st.session_state or st.session_state["universities_df"].empty:
        st.error(
            "University data not loaded. Please run the DGES ETL script to generate universities_2025_1f.csv."
        )
        st.session_state.university_results = []
        return

    df: pd.DataFrame = st.session_state["universities_df"].copy()

    normalized_degree = normalize_text(degree)
    df["course_name_normalized"] = df["course_name"].apply(normalize_text)

    mask = df["course_name_normalized"].str.contains(normalized_degree, case=False, na=False)

    if location != "All of Portugal":
        mask &= df["region"].eq(location)

    if uni_type:
        mask &= df["type"].isin(uni_type)

    results = df[mask].copy()
    results = results.drop(columns=["course_name_normalized"])

    if len(results) == 0:
        st.warning(
            f"No universities found matching '{degree}' with current filters. "
            "Try broadening your search or using a different keyword."
        )
        st.session_state.university_results = []
        return

    if "last_grade" in results.columns:
        results = results.sort_values("last_grade", ascending=False, na_position="last")

    if ranking == "Top 10":
        results = results.head(10)
    elif ranking == "Top 20":
        results = results.head(20)
    elif ranking == "Top 50":
        results = results.head(50)
    else:
        results = results.head(30)

    universities = []
    for _, row in results.iterrows():
        avg_grade_str = "N/A"
        if "last_grade" in row.index and pd.notna(row.get("last_grade")):
            avg_grade_str = f"{row['last_grade']:.1f}/20"

        lat = row.get("lat", None)
        lon = row.get("lon", None)

        acceptance_rate = "N/A"
        vacancies = row.get("vacancies", None)
        placed = row.get("placed", None)
        if pd.notna(vacancies) and pd.notna(placed) and vacancies > 0:
            rate = (placed / vacancies) * 100
            acceptance_rate = f"{rate:.0f}%"

        duration = "3 years"
        degree_type = row.get("degree_type", "")
        if pd.notna(degree_type):
            degree_type_lower = str(degree_type).lower()
            if "mestrado integrado" in degree_type_lower:
                duration = "5 years"
            elif "mestrado" in degree_type_lower:
                duration = "2 years"

        vacancies_str = str(int(vacancies)) if pd.notna(vacancies) else "N/A"
        placed_str = str(int(placed)) if pd.notna(placed) else "N/A"

        uni_dict = {
            "name": row["institution_name"],
            "program_name": row["course_name"],
            "location": row["region"],
            "type": row["type"],
            "acceptance_rate": acceptance_rate,
            "average_grade_required": avg_grade_str,
            "duration": duration,
            "coordinates": {"lat": lat, "lon": lon} if pd.notna(lat) and pd.notna(lon) else {},
            "highlights": [
                f"Last admitted grade: {avg_grade_str}",
                f"Vacancies: {vacancies_str} | Placed: {placed_str}",
                f"Degree type: {row.get('degree_type', 'N/A')}",
            ],
            "website": "#",
        }
        universities.append(uni_dict)
    
    st.session_state.university_results = universities
    st.success(f"Found {len(universities)} universities matching your criteria!")


def render_university_results():
    """Displaying university results with a map"""

    universities = st.session_state.university_results
    user_id = get_user_id()

    if not universities:
        st.info("No results to display. Try different filters.")
        return

    st.markdown("---")
    st.subheader(f"Found {len(universities)} Universities")

    universities_with_coords = [
        u for u in universities if u.get("coordinates") and u["coordinates"].get("lat")
    ]

    if universities_with_coords:
        st.subheader("𖦏 University Locations")
        m = folium.Map(location=[39.5, -8.0], zoom_start=7)
        for uni in universities_with_coords:
            coords = uni["coordinates"]
            popup_html = f"""
            <div style="font-family: 'DMSans', sans-serif; min-width: 200px;">
                <h4 style="color: #558B2F; margin-bottom: 5px;">{uni['name']}</h4>
                <p style="margin: 5px 0;"><strong>{uni['program_name']}</strong></p>
                <p style="margin: 3px 0;">𖦏 {uni['location']}</p>
                <p style="margin: 3px 0;">☰ Last Grade: {uni['average_grade_required']}</p>
            </div>
            """
            folium.Marker(
                [coords["lat"], coords["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="green", icon="graduation-cap", prefix="fa"),
            ).add_to(m)

        st_folium(m, width=700, height=500)
    else:
        st.info("Map view unavailable - coordinate data not loaded for these universities.")

    st.markdown("---")
    st.subheader("☰ University Details")

    for idx, uni in enumerate(universities):
        with st.expander(f"𖠿 {uni['name']} - {uni['program_name']}", expanded=(idx < 3)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**𖤣 Location:** {uni['location']}")
                st.markdown(f"**☰ Type:** {uni['type']}")
                # st.markdown(f"** Last Admitted Grade:** {uni['average_grade_required']}")
            with col2:
                st.markdown(f"**⏱ Duration:** {uni['duration']}")
                # if uni.get("website") and uni["website"] != "#":
                    # st.markdown(f"**Website:** [{uni['name']}]({uni['website']})")

            st.markdown("**ℹ Program Info:**")
            for highlight in uni.get("highlights", []):
                st.markdown(f"- {highlight}")

            student_avg = get_student_admission_average()
            if student_avg is not None and uni["average_grade_required"] != "N/A":
                try:
                    # Parsing required grade
                    req_str = uni["average_grade_required"].split("/")[0].strip()
                    required_grade_raw = float(req_str)
                    # Normalizing to 0-20 scale
                    required_grade = required_grade_raw / 10.0 if required_grade_raw > 20 else required_grade_raw
                    
                    # Normalizing student grade to 0-20 (in case it's still 0-200)
                    student_norm = student_avg / 10.0 if student_avg > 20 else student_avg
                    
                    diff = student_norm - required_grade
                    
                    if diff >= 0:
                        st.success(
                            f"✓ Your average ({student_norm:.2f}/20) meets the requirement "
                            f"({required_grade:.2f}/20) (+{diff:.2f} points)!"
                        )
                    elif diff >= -1.0:
                        st.warning(
                            f" ⚠︎ You're very close! Your average ({student_norm:.2f}/20) is slightly below "
                            f"({required_grade:.2f}/20) ({abs(diff):.2f} points)"
                        )
                    else:
                        gap = abs(diff)
                        st.error(
                            f"⃠ Grade gap... You have {student_norm:.2f}/20, "
                            f"and need {required_grade:.2f}/20 (+{gap:.2f} points)"
                        )
                except:
                    st.info("Grade comparison unavailable for this university")


            elif "student_grades_data" in st.session_state:
                st.info(
                    "ⓘ Complete your exam grades in Grades Analysis to see precise admission chances!"
                )

            col1, col2 = st.columns(2)
            with col1:
                already_saved = is_university_saved(user_id, uni["name"], uni["program_name"])
                if already_saved:
                    st.button(
                        "✓ Saved",
                        key=f"saved_{idx}_{uni['name']}",
                        disabled=True,
                        width='stretch',
                    )
                else:
                    if st.button(
                        "🗂️ Save", key=f"save_{idx}_{uni['name']}", width='stretch'
                    ):
                        # Saving to the saved_universities table
                        if save_university(user_id, uni):
                            # and also saving to My Reports
                            save_single_university_to_reports(user_id, uni)
                            st.success("Saved to your list and My Reports!")
                            st.rerun()
                        else:
                            st.warning("Already in your saved list!")
'''            with col2:
                if uni.get("website") and uni["website"] != "#":
                    st.link_button(
                        " Visit Website", uni["website"], width='stretch'
                    )'''
                    
                    
def save_single_university_to_reports(user_id, uni):
    """Saving a single university to the My Reports section"""

    # generating report content for this university
    report_content = f"""# {uni['name']}

## Program: {uni['program_name']}

### Quick Info
- **Location:** {uni['location']}
- **Type:** {uni['type']}
- **Last Admitted Grade:** {uni['average_grade_required']}
- **Duration:** {uni['duration']}
- **Acceptance Rate:** {uni.get('acceptance_rate', 'N/A')}

### Program Highlights
"""
    
    for highlight in uni.get('highlights', []):
        report_content += f"- {highlight}\n"
    
    # adding a student comparison if available
    student_avg = get_student_admission_average()
    if student_avg and uni["average_grade_required"] != "N/A":
        try:
            required_grade = float(uni["average_grade_required"].split("/")[0])
            report_content += f"\n### Your Admission Chances\n"
            report_content += f"- **Your Average:** {student_avg:.1f}/20\n"
            report_content += f"- **Required Grade:** {required_grade:.1f}/20\n"
            
            diff = student_avg - required_grade
            if diff >= 0:
                report_content += f"- **Status:** ✓ You meet the requirement (+{diff:.1f} points)\n"
            else:
                report_content += f"- **Status:** ⚠︎ Need to improve by {abs(diff):.1f} points\n"
        except:
            pass
    
    report_content += f"\n---\n*Saved from University Finder on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    
    # saving to reports with course name in title for easy extraction
    try:
        save_report(
            user_id=user_id,
            report_type="university",
            title=f"University - {uni['program_name']} - {uni['name']} - {datetime.now().strftime('%Y-%m-%d')}",
            content=report_content,
            cv_data=None
        )
        return True
    except Exception as e:
        st.error(f"Could not save to reports: {e}")
        return False                    
