import streamlit as st
from utils.database import load_reports, delete_report
from services.langfuse_helper import get_user_id


def load_user_reports(user_id):
    """Loading all reports from db into session_state"""
    if "reports" not in st.session_state:
        st.session_state.reports = {}
    
    # professional reports from our database
    st.session_state.reports["professional_cv"] = load_reports(user_id, "professional_cv")
    st.session_state.reports["professional_career_quiz"] = load_reports(user_id, "professional_career_quiz")

    # student reports from our database
    st.session_state.reports["degree"] = load_reports(user_id, "degree")
    st.session_state.reports["career_quiz"] = load_reports(user_id, "career_quiz")
    st.session_state.reports["grades"] = load_reports(user_id, "grades")


def render_reports_center_student():
    # checking login
    # if "username" not in st.session_state:
       # st.warning("⚠︎ Please log in first!")
       # return
    
    user_id = get_user_id()
    load_user_reports(user_id)

    st.header("✉ My Reports")
    tabs = st.tabs(["Degree Picker", "Career Quiz", "Grades"])
    
    # degree tab from our database
    with tabs[0]:
        reports = st.session_state.reports.get("degree", [])
        if not reports:
            st.info("No degree reports yet.")
        else:
            for r in reports:
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander(r["title"]):
                        st.markdown(r["content"])
                with col2:
                    if st.button("🗑️", key=f"deg_del_{r['id']}", help="Delete this report"):
                        delete_report(r["id"])
                        st.success("Deleted!")
                        st.rerun()
    
    # career quiz tab from our database
    with tabs[1]:
        reports = st.session_state.reports.get("career_quiz", [])
        if not reports:
            st.info("No career quiz reports yet.")
        else:
            for r in reports:
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander(r["title"]):
                        st.markdown(r["content"])
                with col2:
                    if st.button("🗑️", key=f"cq_del_{r['id']}", help="Delete this report"):
                        delete_report(r["id"])
                        st.success("Deleted!")
                        st.rerun()
    
    # grades tab from our database
    with tabs[2]:
        reports = st.session_state.reports.get("grades", [])
        if not reports:
            st.info("No grades analyses yet.")
        else:
            for r in reports:
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander(r["title"]):
                        st.markdown(r["content"])
                with col2:
                    if st.button("🗑️", key=f"gr_del_{r['id']}", help="Delete this report"):
                        delete_report(r["id"])
                        st.success("Deleted!")
                        st.rerun()


def render_reports_center_professional():
    # checkintg login
    #if "username" not in st.session_state or not st.session_state.username:
        #st.warning("⚠︎ Please log in first!")
        #return
    
    user_id = st.session_state.username
    
    load_user_reports(user_id)
    
    st.header("✉ My Reports")

    # CV selector
    cv_reports = st.session_state.reports.get("professional_cv", [])
    if cv_reports:
        cv_options = {r["title"]: r.get("cv_data", {}) for r in cv_reports}
        selected_cv = st.selectbox("Use CV:", ["None"] + list(cv_options.keys()), key="prof_cv_selector")
        if selected_cv != "None":
            st.session_state.cv_data = cv_options[selected_cv]
            st.session_state.selected_cv_data = cv_options[selected_cv]
        else:
            st.session_state.selected_cv_data = {}
    
    tab_cv, tab_cq = st.tabs(["CV Analysis", "Career Growth Quiz"])
    
    with tab_cv:
        reports = cv_reports
        if not reports:
            st.info("No CV analysis reports yet!")
        else:
            for r in reports:
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander(r["title"]):
                        st.markdown(r["content"])
                        
                        # showingCV data if available
                        if r.get("cv_data"):
                            st.divider()
                            st.caption("CV Data:")
                            for key, value in r["cv_data"].items():
                                if value and value != "N/A":
                                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                with col2:
                    if st.button("🗑️", key=f"pcv_del_{r['id']}", help="Delete this report"):
                        delete_report(r["id"])
                        st.success("Deleted!")
                        st.rerun()
    
    with tab_cq:
        reports = st.session_state.reports.get("professional_career_quiz", [])
        if not reports:
            st.info("No career growth quiz reports yet!")
        else:
            for r in reports:
                col1, col2 = st.columns([5, 1])
                with col1:
                    with st.expander(r["title"]):
                        st.markdown(r["content"])
                with col2:
                    if st.button("🗑️", key=f"pcq_del_{r['id']}", help="Delete this report"):
                        delete_report(r["id"])
                        st.success("Deleted!")
                        st.rerun()

