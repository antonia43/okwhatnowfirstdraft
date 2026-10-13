import re
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import unicodedata
import json
import os
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
from services.langfuse_helper import LangfuseGeminiWrapper, get_user_id, get_session_id
from datetime import datetime
import traceback


init_database()

GEMINI = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)


def get_student_admission_average():
    """Load CIF from grades reports (JSON format)"""
    user_id = get_user_id()

    try:
        grades_reports = load_reports(user_id, "grades")

        if not grades_reports:
            return None
            
        latest_report = grades_reports[0]
        report_data = json.loads(latest_report['content'])

        if "final_cif" in report_data:
            return report_data["final_cif"]

        elif "student_grades_data" in report_data:
            gradesdata = report_data["student_grades_data"]
            
            if not gradesdata:
                return None
                
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

    except Exception as e:
        print(f"Grade parse error: {e}")
        return None


def normalize_text(text):
    """Remove accents and normalize text for matching"""
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower()


def extract_degrees_from_report(content):
    """Extract degree names from markdown report content"""
    pattern = r'###\s*\d+\.\s*([^(]+?)\s*\('
    degree_matches = re.findall(pattern, content)

    if degree_matches:
        clean_degrees = [d.strip() for d in degree_matches if len(d.strip()) > 3]
        return clean_degrees
    return []


def select_degree_section():
    """Unified degree selection UI for both Portuguese and International modes"""
    user_id = get_user_id()
    degree_reports = load_reports(user_id, "degree")
    has_degree_reports = bool(degree_reports)

    use_report = False
    degree = ""

    if has_degree_reports:
        use_report = st.checkbox(
            "Use degree from My Reports",
            value=True,
            key="degree_use_report",
        )

    if use_report and has_degree_reports:
        report_titles = [r["title"] for r in degree_reports]
        selected_report_title = st.selectbox(
            "Select your degree report:",
            report_titles,
            key="degree_report_selector",
        )

        selected_report = next(r for r in degree_reports if r["title"] == selected_report_title)
        content = selected_report.get("content", "")
        clean_degrees = extract_degrees_from_report(content)

        if clean_degrees:
            degree = st.selectbox(
                "Pick a degree from your report:",
                clean_degrees,
                key="degree_from_report_select",
            )
        else:
            st.warning("Could not extract degrees. Showing report content - copy/paste a degree name below.")
            with st.expander("View Report Content"):
                st.markdown(content)
            use_report = False

    if not use_report:
        if "last_degree_input" not in st.session_state:
            st.session_state.last_degree_input = ""
        if "last_degree_select" not in st.session_state:
            st.session_state.last_degree_select = ""

        common_degrees = [
            "Computer Science",
            "Data Science",
            "Engineering",
            "Business Administration",
            "Psychology",
            "Medicine",
            "Law",
            "Economics",
            "Architecture",
            "Biology",
        ]

        col1, col2 = st.columns([2, 1])
        with col1:
            degree_input = st.text_input(
                "Type your degree:",
                placeholder="e.g., Computer Science, Data Science",
                value=st.session_state.last_degree_input,
                key="degree_manual_input",
            )
        with col2:
            dropdown_index = 0
            if st.session_state.last_degree_select in common_degrees:
                dropdown_index = common_degrees.index(st.session_state.last_degree_select) + 1

            degree_select = st.selectbox(
                "Or pick from popular degrees:",
                [""] + common_degrees,
                index=dropdown_index,
                key="degree_dropdown_select",
            )

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

    return degree


def search_universities_gemini(degree, country, city, preferences):
    """Search international universities using Gemini 2.5 Flash with web search"""

    location_str = ""
    if city and country and country != "Any Country":
        location_str = f"in {city}, {country}"
    elif country and country != "Any Country":
        location_str = f"in {country}"
    else:
        location_str = "worldwide"

    pref_str = f"\n\nAdditional requirements: {preferences}" if preferences else ""

    prompt = f"""Search the web for universities offering {degree} programs {location_str}.

Find up to 20 universities that match the criteria. For each university provide:
- University official name
- Full program name for {degree}
- Country and city location
- Admission requirements (GPA, test scores, prerequisites if available)
- Annual tuition fees in local currency or EUR
- Application deadlines for 2026/2027 academic year
- QS or THE world ranking if available
- Program duration in years
- Primary language of instruction

Focus on accredited universities with programs taught in English or the local language.{pref_str}

If specific information is not available, use "N/A" for that field.

Return your response as valid JSON with this exact structure:
{{
  "universities": [
    {{
      "name": "University Name",
      "program_name": "Program Name",
      "country": "Country",
      "city": "City",
      "admission_requirements": "Requirements text",
      "tuition_annual": "Amount",
      "application_deadline": "Date",
      "ranking": "QS/THE ranking or N/A",
      "program_duration": "Years",
      "language_of_instruction": "Language"
    }}
  ]
}}

Return ONLY the JSON, no other text or markdown formatting."""

    try:
        response = GEMINI.generate_content(
            prompt=prompt,
            temperature=0.5,
            user_id=get_user_id(),
            session_id=get_session_id()
        )

        cleaned = response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        cleaned = cleaned.strip()

        results = json.loads(cleaned)

        if "universities" not in results:
            st.error(f"Invalid response structure from AI")
            return {"universities": []}

        return results

    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response: {str(e)}")
        return {"universities": []}
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        traceback.print_exc()
        return {"universities": []}


def render_university_finder():
    """Main university finder with Portugal and International buttons"""
    st.header("𖤣 University Finder")

    user_id = get_user_id()

    if "university_finder_mode" not in st.session_state:
        st.session_state.university_finder_mode = None

    st.subheader("Where are you planning to study?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Portugal", width="stretch", type="primary" if st.session_state.university_finder_mode == "Portugal" else "secondary"):
            st.session_state.university_finder_mode = "Portugal"
            st.rerun()
    with col2:
        if st.button("International", width="stretch", type="primary" if st.session_state.university_finder_mode == "International" else "secondary"):
            st.session_state.university_finder_mode = "International"
            st.rerun()

    if st.session_state.university_finder_mode == "Portugal":
        render_portuguese_finder()
    elif st.session_state.university_finder_mode == "International":
        render_international_finder()
    else:
        st.info("ⓘ Please select an option to continue")


def render_portuguese_finder():
    """Portuguese university finder using DGES data"""
    user_id = get_user_id()

    degree_reports = load_reports(user_id, "degree")
    has_degree_reports = bool(degree_reports)

    if not has_degree_reports:
        st.info(
            "ⓘ Complete the Degree Picker first to get personalized degree ideas, "
            "or search universities directly below."
        )
        if st.button("Go to Degree Picker", width="stretch"):
            st.session_state.redirect_to = "Degree Picker"
            st.rerun()
        st.markdown("---")

    # FIXED: Filter saved universities to only show Portuguese ones
    saved_universities = get_saved_universities(user_id)
    portuguese_unis = [uni for uni in saved_universities if uni.get('type') != 'International']
    
    if portuguese_unis:
        with st.expander(f"Your Saved Portuguese Universities ({len(portuguese_unis)})", expanded=False):
            for uni in portuguese_unis:
                col1, col2 = st.columns([5, 6])
                with col1:
                    st.write(
                        f"**{uni['name']}** - {uni['program_name']} "
                        f"({uni['average_grade_required']})"
                    )
                with col2:
                    if st.button(
                        "Remove",
                        key=f"remove_{uni['name']}_{uni['program_name']}",
                    ):
                        if remove_saved_university(user_id, uni["name"], uni["program_name"]):
                            st.success("Removed!")
                            st.rerun()

            if st.button("Clear All Portuguese Universities", type="secondary"):
                for uni in portuguese_unis:
                    remove_saved_university(user_id, uni["name"], uni["program_name"])
                st.success("Cleared Portuguese universities")
                st.rerun()

        st.markdown("---")

    st.subheader("What degree are you looking for?")
    use_report = False
    degree = ""

    if has_degree_reports:
        use_report = st.checkbox(
            "Use degree from My Reports",
            value=True,
            key="uf_use_report",
        )

    if use_report and has_degree_reports:
        report_titles = [r["title"] for r in degree_reports]
        selected_report_title = st.selectbox(
            "Select your degree report:",
            report_titles,
            key="uf_report_selector",
        )

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
                "Type your degree:",
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
        st.info("Enter or select a degree to start searching")
        return

    st.success(f"Searching for universities offering **{degree}**")
    st.markdown("---")

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
        if st.button("Search Universities", width="stretch", type="primary"):
            search_universities(degree, location, uni_type, ranking, show_grade_filter, grade_margin)
            st.rerun()

    if "university_results" in st.session_state and st.session_state.university_results:
        render_university_results()


def search_universities(degree, location, uni_type, ranking, show_grade_filter=True, grade_margin=0.5):
    """Search universities using local DGES CSV data"""

    if "universities_df" not in st.session_state or st.session_state["universities_df"].empty:
        st.error(
            "University data not loaded. Please run the DGES ETL script to generate universities_2025_1f.csv."
        )
        st.session_state.university_results = []
        return

    df = st.session_state["universities_df"].copy()

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
    st.success(f"Found {len(universities)} universities matching your criteria")


def render_university_results():
    """Display Portuguese university results with map"""

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
        st.subheader("University Locations")
        m = folium.Map(location=[39.5, -8.0], zoom_start=7)
        for uni in universities_with_coords:
            coords = uni["coordinates"]
            popup_html = f"""
            <div style="font-family: 'DMSans', sans-serif; min-width: 200px;">
                <h4 style="color: #558B2F; margin-bottom: 5px;">{uni['name']}</h4>
                <p style="margin: 5px 0;"><strong>{uni['program_name']}</strong></p>
                <p style="margin: 3px 0;">{uni['location']}</p>
                <p style="margin: 3px 0;">Last Grade: {uni['average_grade_required']}</p>
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
    st.subheader("University Details")

    for idx, uni in enumerate(universities):
        with st.expander(f"{uni['name']} - {uni['program_name']}", expanded=(idx < 3)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Location:** {uni['location']}")
                st.markdown(f"**Type:** {uni['type']}")
            with col2:
                st.markdown(f"**Duration:** {uni['duration']}")

            st.markdown("**Program Info:**")
            for highlight in uni.get("highlights", []):
                st.markdown(f"- {highlight}")

            student_avg = get_student_admission_average()
            if student_avg is not None and uni["average_grade_required"] != "N/A":
                try:
                    req_str = uni["average_grade_required"].split("/")[0].strip()
                    required_grade_raw = float(req_str)
                    required_grade = required_grade_raw / 10.0 if required_grade_raw > 20 else required_grade_raw

                    student_norm = student_avg / 10.0 if student_avg > 20 else student_avg

                    diff = student_norm - required_grade

                    if diff >= 0:
                        st.success(
                            f"Your average ({student_norm:.2f}/20) meets the requirement "
                            f"({required_grade:.2f}/20) (+{diff:.2f} points)"
                        )
                    elif diff >= -1.0:
                        st.warning(
                            f"You're close! Your average ({student_norm:.2f}/20) is slightly below "
                            f"({required_grade:.2f}/20) ({abs(diff):.2f} points)"
                        )
                    else:
                        gap = abs(diff)
                        st.error(
                            f"Grade gap: You have {student_norm:.2f}/20, "
                            f"need {required_grade:.2f}/20 (+{gap:.2f} points)"
                        )
                except:
                    st.info("Grade comparison unavailable for this university")
            elif "student_grades_data" in st.session_state:
                st.info("Complete your exam grades in Grades Analysis to see precise admission chances")

            col1, col2 = st.columns(2)
            with col1:
                already_saved = is_university_saved(user_id, uni["name"], uni["program_name"])
                if already_saved:
                    st.button(
                        "Saved",
                        key=f"saved_{idx}_{uni['name']}",
                        disabled=True,
                        width="stretch",
                    )
                else:
                    if st.button(
                        "Save", key=f"save_{idx}_{uni['name']}", width="stretch"
                    ):
                        if save_university(user_id, uni):
                            save_single_university_to_reports(user_id, uni)
                            st.success("Saved to your list and My Reports")
                            st.rerun()
                        else:
                            st.warning("Already in your saved list")


def render_international_finder():
    """International university search using Gemini with Google Search grounding"""
    st.subheader("International University Search")

    user_id = get_user_id()

    # Show saved international universities
    saved_universities = get_saved_universities(user_id)
    international_unis = [uni for uni in saved_universities if uni.get('type') == 'International']
    
    if international_unis:
        with st.expander(f"Your Saved International Universities ({len(international_unis)})", expanded=False):
            for uni in international_unis:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{uni['name']}** - {uni['program_name']} ({uni['location']})")
                with col2:
                    if st.button("Remove", key=f"remove_intl_{uni['name']}_{uni['program_name']}"):
                        if remove_saved_university(user_id, uni["name"], uni["program_name"]):
                            st.success("Removed!")
                            st.rerun()
            
            if st.button("Clear All International Universities", type="secondary"):
                for uni in international_unis:
                    remove_saved_university(user_id, uni["name"], uni["program_name"])
                st.success("Cleared international universities")
                st.rerun()
        
        st.markdown("---")

    degree = select_degree_section()

    if not degree:
        st.info("Select a degree to start searching")
        return

    st.markdown("---")
    st.subheader("Location Preferences")

    col1, col2 = st.columns(2)
    with col1:
        country_select = st.selectbox(
            "Country:",
            [
                "Any Country",
                "United States",
                "United Kingdom",
                "Germany",
                "Netherlands",
                "Canada",
                "Australia",
                "France",
                "Spain",
                "Italy",
                "Sweden",
                "Denmark",
                "Switzerland",
                "Austria",
                "Belgium",
                "Czech Republic",
                "Poland",
                "Ireland",
                "Norway",
                "Finland",
                "Other"
            ],
            key="intl_country_select"
        )
        
        # Handle "Other" country
        if country_select == "Other":
            country = st.text_input(
                "Enter country name:",
                placeholder="e.g., Japan, South Korea, Singapore",
                key="intl_custom_country"
            )
            if not country.strip():
                country = "Any Country"
        else:
            country = country_select
            
    with col2:
        city_select = st.selectbox(
            "City:",
            [
                "Any City",
                "London",
                "Berlin",
                "Amsterdam",
                "Paris",
                "Barcelona",
                "Munich",
                "Copenhagen",
                "Stockholm",
                "Vienna",
                "Prague",
                "Dublin",
                "Oslo",
                "Helsinki",
                "Other"
            ],
            key="intl_city_select"
        )
        
        # Handle "Other" city
        if city_select == "Other":
            city = st.text_input(
                "Enter city name:",
                placeholder="e.g., Tokyo, Singapore, Dubai",
                key="intl_custom_city"
            )
        elif city_select == "Any City":
            city = ""
        else:
            city = city_select

    preferences = st.text_area(
        "Additional preferences (optional):",
        placeholder="e.g., affordable tuition, English-taught programs, scholarships available, research-focused",
        height=80,
        key="intl_preferences_input"
    )

    if st.button("Search International Universities", type="primary", width="stretch"):
        with st.spinner("Searching for universities..."):
            try:
                results = search_universities_gemini(
                    degree=degree,
                    country=country if country != "Any Country" else None,
                    city=city if city else None,
                    preferences=preferences if preferences else None
                )

                universities = results.get('universities', [])

                if universities:
                    st.session_state.intl_university_results = universities
                    st.success(f"Found {len(universities)} universities")
                    st.rerun()
                else:
                    st.warning("No universities found. Try different search criteria.")

            except Exception as e:
                st.error(f"Search failed: {str(e)}")
                st.code(traceback.format_exc())

    if "intl_university_results" in st.session_state and st.session_state.intl_university_results:
        render_international_results()


def render_international_results():
    """Display international university search results"""
    results = st.session_state.intl_university_results
    user_id = get_user_id()

    if not results:
        st.info("No results to display.")
        return

    st.markdown("---")
    st.subheader(f"Found {len(results)} Universities")

    sort_by = st.radio(
        "Sort by:",
        ["University Name", "Country"],
        horizontal=True,
        key="intl_sort_radio"
    )

    if sort_by == "Country":
        results = sorted(results, key=lambda x: x.get('country', ''))
    else:
        results = sorted(results, key=lambda x: x.get('name', ''))

    for idx, uni in enumerate(results):
        location_display = f"{uni.get('city', '')}, {uni.get('country', '')}" if uni.get('city') else uni.get('country', '')

        with st.expander(f"{uni.get('name', 'N/A')} - {location_display}", expanded=(idx < 3)):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Program:** {uni.get('program_name', 'N/A')}")
                st.markdown(f"**Location:** {location_display}")
                st.markdown(f"**Duration:** {uni.get('program_duration', 'N/A')}")

                if uni.get('language_of_instruction'):
                    st.markdown(f"**Language:** {uni['language_of_instruction']}")

                if uni.get('ranking') and uni['ranking'] != 'N/A':
                    st.markdown(f"**Ranking:** {uni['ranking']}")

                if uni.get('tuition_annual') and uni['tuition_annual'] != 'N/A':
                    st.markdown(f"**Tuition:** {uni['tuition_annual']}")

                if uni.get('admission_requirements') and uni['admission_requirements'] != 'N/A':
                    st.markdown("**Admission Requirements:**")
                    st.info(uni['admission_requirements'])

                if uni.get('application_deadline') and uni['application_deadline'] != 'N/A':
                    st.markdown(f"**Application Deadline:** {uni['application_deadline']}")

            with col2:
                already_saved = is_university_saved(user_id, uni.get('name', ''), uni.get('program_name', ''))
                if already_saved:
                    st.button("Saved", key=f"intl_saved_{idx}", disabled=True)
                else:
                    if st.button("Save", key=f"intl_save_{idx}"):
                        formatted_uni = {
                            "name": uni.get('name', 'N/A'),
                            "program_name": uni.get('program_name', 'N/A'),
                            "location": uni.get('country', 'N/A'),
                            "type": "International",
                            "acceptance_rate": "N/A",
                            "average_grade_required": "N/A",
                            "duration": uni.get('program_duration', 'N/A'),
                            "coordinates": {},
                            "highlights": [
                                f"Ranking: {uni.get('ranking', 'N/A')}",
                                f"Tuition: {uni.get('tuition_annual', 'N/A')}",
                                f"Language: {uni.get('language_of_instruction', 'N/A')}",
                            ],
                            "website": uni.get('website', '#'),
                        }
                        save_university(user_id, formatted_uni)
                        save_single_university_to_reports(user_id, formatted_uni)
                        st.success("Saved")
                        st.rerun()

                if uni.get('website') and uni['website'] not in ['#', 'N/A']:
                    st.link_button("Visit Website", uni['website'], width="stretch")


def save_single_university_to_reports(user_id, uni):
    """Save university to My Reports section"""

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

    student_avg = get_student_admission_average()
    if student_avg and uni["average_grade_required"] != "N/A":
        try:
            required_grade = float(uni["average_grade_required"].split("/")[0])
            report_content += f"\n### Your Admission Chances\n"
            report_content += f"- **Your Average:** {student_avg:.1f}/20\n"
            report_content += f"- **Required Grade:** {required_grade:.1f}/20\n"

            diff = student_avg - required_grade
            if diff >= 0:
                report_content += f"- **Status:** You meet the requirement (+{diff:.1f} points)\n"
            else:
                report_content += f"- **Status:** Need to improve by {abs(diff):.1f} points\n"
        except:
            pass

    report_content += f"\n---\n*Saved from University Finder on {datetime.now().strftime('%Y-%m-%d %H:%M')}*"

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
