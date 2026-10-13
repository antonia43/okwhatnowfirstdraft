from dotenv import load_dotenv
from pages.cv_analysis import render_cv_analysis
from pages.career_growth_quiz import render_career_growth_quiz
from pages.resources import render_resources
from pages.interview_simulator import render_interview_simulator
from pages.cv_builder import render_cv_builder
from pages.professional_chat import render_dashboard_chat
from utils.reports import render_reports_center_professional

load_dotenv()

def render_professional_dashboard(choice: str):
    """
    Rendering the professional dashboard based on sidebar choice.
    """
    
    if choice == "Dashboard":
        render_dashboard_chat()
    
    elif choice == "CV Analysis":
        render_cv_analysis()
    
    elif choice == "Career Growth":
        render_career_growth_quiz()
    
    elif choice == "Your Next Steps":
        render_resources()
    
    elif choice == "Interview Prep":
        render_interview_simulator()
    
    elif choice == "CV Builder":
        render_cv_builder()
    
    elif choice == "My Reports":
        render_reports_center_professional()
