"""The Saved page: what the student kept from the chat, in one place."""
import streamlit as st

from services import chat_functions
from services import chat_helpers as h
from services.langfuse_helper import get_user_id
from utils import database


def _open_chat(conversation_id):
    st.session_state.pending_open = conversation_id
    st.session_state.student_choice = "Chat"


def _delete_chat(conversation_id, user_id):
    database.delete_conversation(conversation_id, user_id)
    if st.session_state.get("conversation_id") == conversation_id:
        st.session_state.pop("conversation_id", None)


def _remove_university(user_id, institution_name, program_name):
    chat_functions.call_function(
        "remove_saved_university", {"institution_name": institution_name, "program_name": program_name}, user_id)
    pins = st.session_state.get("saved_pins")
    if pins is not None:
        pins.discard((institution_name, program_name))


def _quiz_results(user_id):
    for label, report_type, hint in (
        ("Career Discovery quiz", "career_quiz", "Ask the chat to run the Career Discovery quiz."),
        ("Degree quiz", "degree", "Ask the chat to help you narrow down degrees in a field."),
    ):
        st.subheader(label)
        reports = database.load_reports(user_id, report_type)
        if not reports:
            st.caption(f"Nothing saved yet. {hint}")
        for report in reports:
            with st.expander(report["title"]):
                st.markdown(report["content"])
                st.button("Remove", key=f"del_report_{report['id']}", on_click=database.delete_report,
                          args=(report["id"],))


def _universities(user_id):
    out = chat_functions.call_function("get_saved_universities", {}, user_id)
    items = (out.get("result") or {}).get("universities", [])
    if not items:
        st.caption("Nothing saved yet. Ask the chat to find universities for a degree, then save the ones you like.")
        return
    grade = out["result"].get("grade_used_200")
    if grade is not None:
        st.caption(f"Compared with your admission average of {grade:.1f}/200. Last year's cut-off does not guarantee this year's.")
    for i, uni in enumerate(items):
        left, right = st.columns([5, 1])
        chance = h.CHANCE_WORDS.get(uni.get("chance"), "")
        with left:
            st.markdown(f"**{uni['institution_name']}**  \n{uni['program_name']} · {uni.get('region', '')}  \n"
                        f"Last placed: {h.grade_text(uni)}" + (f" · **{chance}**" if chance else ""))
        with right:
            st.button("Remove", key=f"rm_uni_{i}", on_click=_remove_university,
                      args=(user_id, uni["institution_name"], uni["program_name"]), width="stretch")


def _grades(user_id):
    out = chat_functions.call_function("get_saved_grades", {}, user_id)
    result = out.get("result") or {}
    if not result.get("has_grades"):
        st.caption("No grades saved yet. Tell the chat your grades or attach a screenshot, and ask it to save them.")
        return
    st.metric("Admission average (CIF)", f"{result['cif_200']:.1f} / 200", f"{result['cif_200'] / 10:.2f} / 20",
              delta_color="off")
    for period, label in (("10th", "10th grade"), ("11th", "11th grade"), ("12th", "12th grade"), ("exams", "National exams")):
        subjects = (result.get("grades_data", {}).get("grades", {}) or {}).get(period) or {}
        if subjects:
            st.markdown(f"**{label}**")
            st.table({"Subject": list(subjects), "Grade": [f"{g:g}" for g in subjects.values()]})


def _chats(user_id):
    groups = h.group_conversations(database.get_conversations(user_id))
    if not groups:
        st.caption("No saved chats yet. Your conversations are saved here automatically when you are logged in.")
        return
    for tag, conversations in groups.items():
        st.subheader(tag)
        for conv in conversations:
            left, middle, right = st.columns([5, 1, 1])
            with left:
                st.markdown(f"{conv['text']}  \n<small>{conv['updated_at'][:16]}</small>", unsafe_allow_html=True)
            with middle:
                st.button("Open", key=f"open_{conv['id']}", on_click=_open_chat, args=(conv["id"],), width="stretch")
            with right:
                st.button("Delete", key=f"del_chat_{conv['id']}", on_click=_delete_chat, args=(conv["id"], user_id),
                          width="stretch")


def render_saved():
    st.header("Saved")
    user_id = get_user_id()
    if chat_functions.is_guest(user_id):
        st.info("Guests can't save anything. Log in or register to keep your quiz results, universities, grades and chats.")
        return
    quizzes, universities, grades, chats = st.tabs(["Quiz results", "Universities", "Grades", "Chats"])
    with quizzes:
        _quiz_results(user_id)
    with universities:
        _universities(user_id)
    with grades:
        _grades(user_id)
    with chats:
        _chats(user_id)
