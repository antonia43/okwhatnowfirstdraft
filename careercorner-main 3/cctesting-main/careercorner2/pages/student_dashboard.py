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

    # student chat/tools are available right after login
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
