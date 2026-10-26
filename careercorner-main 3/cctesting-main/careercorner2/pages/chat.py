"""The chat page: one conversation that can use every ability.

All the thinking lives in services/chat_engine.py. This page only draws the conversation,
the map for university searches, and the buttons.
"""
import traceback

import folium
import streamlit as st
from streamlit_folium import st_folium

from services import chat_engine, chat_functions
from services import chat_helpers as h
from services.langfuse_helper import get_user_id
from utils import database
from utils.gemini_key import get_gemini_api_key

ADAPTER = None  # tests put a fake model here
ACCEPTED_FILES = ["png", "jpg", "jpeg", "pdf"]
MIME_BY_SUFFIX = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "pdf": "application/pdf"}
OPENING = {"role": "assistant", "content": chat_engine.OPENING_MESSAGE, "opening": True}
LEGEND = "Pin colours: green = safe, yellow = target, red = reach, grey = no grade or no cut-off to compare."


# ---- state ---------------------------------------------------------------------

def start_new_chat():
    """Forget the current conversation and begin a fresh one."""
    for key in ("chat_messages", "chat_session", "conversation_id", "chat_tag", "chat_first", "saved_pins"):
        st.session_state.pop(key, None)
    st.session_state.upload_round = st.session_state.get("upload_round", 0) + 1


def _init():
    ss = st.session_state
    ss.setdefault("chat_session", {})
    ss.setdefault("conversation_id", None)
    ss.setdefault("chat_tag", h.GENERAL)
    ss.setdefault("chat_first", "")
    ss.setdefault("upload_round", 0)
    if "chat_messages" not in ss:
        ss.chat_messages = [dict(OPENING)]


def open_conversation(conversation_id, user_id):
    """Load an earlier chat from the database so the student can carry on."""
    ss = st.session_state
    title = next((c["title"] for c in database.get_conversations(user_id) if c["id"] == conversation_id), "")
    tag, text = h.split_title(title)
    messages = database.get_messages(conversation_id, user_id)
    ss.chat_messages = [dict(OPENING)] + [{"role": m["role"], "content": m["content"]} for m in messages]
    ss.chat_session = {}
    ss.conversation_id = conversation_id
    ss.chat_tag = tag
    ss.chat_first = text


def _saved_pins(user_id):
    ss = st.session_state
    if "saved_pins" not in ss:
        ss.saved_pins = set()
        if not chat_functions.is_guest(user_id):
            for uni in database.get_saved_universities(user_id) or []:
                ss.saved_pins.add((uni.get("name", ""), uni.get("program_name", "")))
    return ss.saved_pins


# ---- the map and the program cards ---------------------------------------------

def _save_pin(user_id, course_code, institution_name, program_name):
    out = chat_functions.call_function(
        "save_university", {"course_code": course_code, "institution_name": institution_name}, user_id)
    result = out.get("result") or {}
    if out.get("ok") and (result.get("saved") or result.get("already_saved")):
        st.session_state.saved_pins.add((institution_name, program_name))
        st.toast("Saved. You can find it under Saved.")
    else:
        st.toast(out.get("error") or result.get("error") or "That could not be saved.")


def _program_card(key, uni, user_id):
    guest = chat_functions.is_guest(user_id)
    pins = _saved_pins(user_id)
    saved = (uni["institution_name"], uni["program_name"]) in pins
    left, right = st.columns([4, 1])
    chance = h.CHANCE_WORDS.get(uni.get("chance"), "")
    with left:
        st.markdown(f"**{uni['institution_name']}**  \n{uni['program_name']} · {uni.get('region', '')}  \n"
                    f"Last placed: {h.grade_text(uni)}" + (f" · **{chance}**" if chance else ""))
    with right:
        if guest:
            st.caption("Log in to save")
        else:
            st.button("Saved" if saved else "Save", key=f"save_{key}", disabled=saved, width="stretch",
                      on_click=_save_pin,
                      args=(user_id, uni["course_code"], uni["institution_name"], uni["program_name"]))


def _render_map(key, result, user_id):
    universities = result.get("universities", [])
    if not universities:
        st.info(result.get("message") or "No programs found.")
        return
    points = h.map_points(result)
    caption = f"Showing {result.get('shown', len(universities))} of {result.get('total_found', len(universities))} programs."
    if result.get("grade_used_200") is not None:
        caption += f" Compared with your grade of {result['grade_used_200']:.1f}/200. {LEGEND}"
    st.caption(caption)

    clicked = None
    if points:
        fmap = folium.Map(location=[39.5, -8.0], zoom_start=6)
        for p in points:
            popup = (f"<div style='min-width:200px'><b>{p['institution_name']}</b><br>{p['program_name']}<br>"
                     f"{p.get('region', '')}<br>Last placed: {h.grade_text(p)}</div>")
            folium.CircleMarker(
                [p["lat"], p["lon"]], radius=9, color="#ffffff", weight=2, fill=True,
                fill_color=p["hex"], fill_opacity=0.95, tooltip=h.pin_label(p),
                popup=folium.Popup(popup, max_width=300),
            ).add_to(fmap)
        out = st_folium(fmap, width=700, height=420, returned_objects=["last_object_clicked_tooltip"],
                        key=f"map_{key}")
        clicked = (out or {}).get("last_object_clicked_tooltip")
    else:
        st.info("None of these programs have a map position yet, so they are listed below.")
    if result.get("without_map_pin"):
        st.caption(f"{result['without_map_pin']} program(s) have no map position and are only in the list.")

    selected = next((u for u in universities if h.pin_label(u) == clicked), None)
    if selected:
        st.markdown("**Selected on the map**")
        _program_card(f"{key}_sel", selected, user_id)
    with st.expander(f"All {len(universities)} programs"):
        for i, uni in enumerate(universities):
            _program_card(f"{key}_{i}", uni, user_id)


def _render_message(index, message, user_id):
    with st.chat_message(message["role"]):
        if message.get("file"):
            st.caption(f"Attached: {message['file']}")
        st.markdown(message["content"])
        for j, event in enumerate(message.get("events", [])):
            result = event.get("result") or {}
            if event.get("ok") and result.get("display") == "map":
                _render_map(f"{index}_{j}", result, user_id)


# ---- saving the conversation -----------------------------------------------------

def _persist(user_id, prompt, answer, events):
    """Keep the conversation for logged-in students. Guests' chats only live in this session."""
    ss = st.session_state
    if chat_functions.is_guest(user_id):
        return
    previous = ss.chat_tag
    ss.chat_tag = h.conversation_tag(events, ss.chat_tag)
    if ss.conversation_id is None:
        ss.chat_first = prompt
        ss.conversation_id = database.create_conversation(user_id, h.make_title(ss.chat_tag, prompt))
    elif ss.chat_tag != previous:
        database.rename_conversation(ss.conversation_id, user_id, h.make_title(ss.chat_tag, ss.chat_first))
    if ss.conversation_id:
        database.add_message(ss.conversation_id, user_id, "user", prompt)
        database.add_message(ss.conversation_id, user_id, "assistant", answer)


def _adapter():
    if ADAPTER is not None:
        return ADAPTER
    return _real_adapter(get_gemini_api_key())


@st.cache_resource
def _real_adapter(api_key):
    return chat_engine.GeminiAdapter(api_key)


# ---- the page ----------------------------------------------------------------------

def render_chat():
    _init()
    ss = st.session_state
    user_id = get_user_id()
    guest = chat_functions.is_guest(user_id)

    pending = ss.pop("pending_open", None)
    if pending is not None and not guest:
        open_conversation(pending, user_id)

    if guest:
        st.caption("You're chatting as a guest. Log in or register to save your results and chats.")

    for i, message in enumerate(ss.chat_messages):
        _render_message(i, message, user_id)

    if ADAPTER is None and not get_gemini_api_key():
        st.error("The AI is not set up yet: the Gemini API key is missing from the app's secrets.")
        return

    with st.expander("Attach a screenshot or PDF of your grades"):
        upload = st.file_uploader("Grades file", type=ACCEPTED_FILES, key=f"upload_{ss.upload_round}",
                                  label_visibility="collapsed")
        st.caption("It is only used to read your grades. I'll show you what I read so you can check it.")

    prompt = st.chat_input("Ask me anything about studying in Portugal")
    if not prompt:
        return

    image, file_name = None, None
    if upload is not None:
        suffix = upload.name.rsplit(".", 1)[-1].lower()
        image = {"bytes": upload.getvalue(), "mime": upload.type or MIME_BY_SUFFIX.get(suffix, "image/png")}
        file_name = upload.name

    history = [{"role": m["role"], "content": m["content"]} for m in ss.chat_messages if not m.get("opening")]
    with st.chat_message("user"):
        if file_name:
            st.caption(f"Attached: {file_name}")
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                out = chat_engine.run_turn(_adapter(), history, prompt, user_id, ss.chat_session, image=image)
            except Exception:
                traceback.print_exc()
                out = {"text": "I couldn't reach the AI just now. Please try again in a moment.", "events": []}

    ss.chat_messages.append({"role": "user", "content": prompt, "file": file_name})
    ss.chat_messages.append({"role": "assistant", "content": out["text"], "events": out["events"]})
    _persist(user_id, prompt, out["text"], out["events"])
    ss.upload_round += 1  # clears the file box
    st.rerun()
