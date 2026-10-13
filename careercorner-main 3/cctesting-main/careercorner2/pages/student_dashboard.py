import streamlit as st
from dotenv import load_dotenv
from pages.student_chat import render_dashboard_chat
from pages.student_career_quiz import render_student_career_quiz
from pages.grades_analysis import render_grades_analysis
from pages.degree_picker import render_degree_picker
from utils.reports import render_reports_center_student
from pages.student_resources import render_student_resources
from pages.university_finder import render_university_finder

load_dotenv()


def render_student_dashboard(choice: str):
    """
    Render the student dashboard based on sidebar choice.

    choice: "Dashboard", "Career Quiz", "Degree Picker",
            "Grades Analysis", "University Finder"
    """

    # init onboarding flag
    if "student_onboarding_done" not in st.session_state:
        st.session_state.student_onboarding_done = False

    # onboarding gate to block all student tools until the user confirms they are students
    if not st.session_state.student_onboarding_done:
        st.header("Student Dashboard")
        st.info(
            """
            This section is for **high school students** who are:
            
            ⟡ Planning to go to university  
            ⟡ Exploring degrees and study paths  
            ⟡ Comparing universities and entry grades  
            
            If you are already in **university** or have **work experience**, 
            you’ll get better support in the **Professional Dashboard**.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "✌︎︎ I'm a High School Student!",
                width='stretch',
                type="primary",
            ):
                st.session_state.student_onboarding_done = True
                st.rerun()
        with col2:
            if st.button(
                "𖠿 Take me to the Professional Dashboard!",
                width='stretch',
            ):
                st.session_state.user_type = "professional"
                st.session_state.student_onboarding_done = False
                st.rerun()

        return  # do not render any student tools yet

    # after onboarding we can route to actual pages
    if choice == "Dashboard":
        render_dashboard_chat()

    elif choice == "Career Quiz":
        render_student_career_quiz()

    elif choice == "Degree Picker":
        render_degree_picker()

    elif choice == "Grades Analysis":
        render_grades_analysis()

    elif choice == "University Finder":
        render_university_finder()
        
    elif choice == "Resources":
        render_student_resources()
        
    elif choice == "My Reports":
        render_reports_center_student()
