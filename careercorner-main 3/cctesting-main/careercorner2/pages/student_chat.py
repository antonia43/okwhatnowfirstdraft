"""The chat: one conversation that can do everything the app does.

The assistant is given every registered chat function (services/chat_functions.py) as a Gemini
tool. When the student asks for something, Gemini calls the function, we run it through
call_function (which supplies the signed-in student's id, blocks guests from saving, and turns
errors into messages), hand the result back, and Gemini writes the answer.

Conversations are saved per account (conversations / messages tables) for signed-in students.
"""
import streamlit as st
from google import genai
from google.genai import types

from services.chat_functions import call_function, get_declarations, is_guest, load_all
from services.langfuse_helper import get_user_id
from utils import database
from utils.gemini_key import get_gemini_api_key

MODEL = "gemini-2.5-flash"
MAX_TOOL_ROUNDS = 8
PLACEHOLDER = "Ask the Okay, now what Assistant anything about your studies!"
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]

STARTERS = [
    ("Find my best-fit career sector", "I don't know what I want to study. Can you help me find out?"),
    ("Work out my admission grade", "Can you calculate my admission grade?"),
    ("Find degrees and universities", "Help me find degrees and universities in Portugal."),
    ("Study resources and exam papers", "Where can I find study resources and past exam papers?"),
]

SYSTEM_INSTRUCTION = """You are the Okay, now what Assistant, a warm, practical study guide for students \
in Portugal who are working out what to study and where. You do the work yourself inside this chat. \
Never send the student to a menu or another page, and never mention function or tool names to them.

WHAT YOU CAN DO (use your functions, don't guess):
- Learn about them: see what is already known (saved grades, quiz results, saved universities, \
preferences) so you never ask something twice. For a signed-in student, check this at the start of \
the conversation. Remember new details they share (year, track, interests, preferred regions).
- Career Discovery quiz for students who don't know what they like. Degree quiz for students who \
already named a field.
- Admission grade: calculate it from grades they type or from a screenshot they attach, check chances \
for a degree, and compare their saved universities with their grade.
- Find Portuguese degree programs on a map, with the last-placed grade and chance colours, and save or \
remove universities from their list.
- Free study resources for any subject, official national exam papers, and scholarships.

HOW TO RUN THINGS
- Quizzes: ask each question exactly as given, one at a time, then pass the student's answer back. \
Show the results clearly when they finish, then offer to save them.
- Grades: read every subject and grade from a screenshot carefully, show what you read and ask them to \
confirm before saving. School grades are 0-20, national exams 0-200, and the admission grade used by \
DGES is on a 0-200 scale. Calculating does not save anything.
- University search: a map appears automatically below your message. Don't list every program. \
Mention the few that matter (best fits, notable reaches) and explain the colours: green is a high \
chance, yellow possible, red low.
- Only save when the student wants it. Guests can use everything except saving; if a guest wants to \
save, tell them kindly to log in or register first.
- Use only what the functions return. Never make up cut-off grades, universities, links or \
deadlines. If a function reports an error or no result, say so plainly and offer another way forward.

STYLE: friendly, short, one question at a time, plain language. You only help students with studies \
and degree choices."""


# ---------------------------------------------------------------- state

def _init_state():
    st.session_state.setdefault("chat_messages", [])  # what is shown: role, content, maps
    st.session_state.setdefault("chat_contents", [])  # what Gemini sees (includes function calls)
    st.session_state.setdefault("chat_scratch", {})  # quiz progress etc., lives for one conversation
    st.session_state.setdefault("chat_conversation_id", None)


def _reset_chat():
    st.session_state.chat_messages = []
    st.session_state.chat_contents = []
    st.session_state.chat_scratch = {}
    st.session_state.chat_conversation_id = None


def _load_conversation(user_id, conversation_id):
    rows = database.get_messages(conversation_id, user_id)
    _reset_chat()
    st.session_state.chat_conversation_id = conversation_id
    for row in rows:
        st.session_state.chat_messages.append({"role": row["role"], "content": row["content"], "maps": []})
        role = "user" if row["role"] == "user" else "model"
        st.session_state.chat_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=row["content"])]))


# ---------------------------------------------------------------- Gemini loop

def _tools():
    declarations = [types.FunctionDeclaration(**d) for d in get_declarations()]
    return [types.Tool(function_declarations=declarations)]


def _text_of(content):
    return "".join(p.text for p in (content.parts or []) if getattr(p, "text", None)).strip()


def run_turn(client, contents, user_id, scratch, model=MODEL):
    """Send the conversation to Gemini and run any functions it asks for until it answers.

    contents is extended in place with everything that happened. Returns (answer, maps).
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.4,
        tools=_tools(),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    maps = []
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.models.generate_content(model=model, contents=contents, config=config)
        candidate = response.candidates[0] if response.candidates else None
        if candidate is None or candidate.content is None or not candidate.content.parts:
            return "Sorry, I couldn't come up with an answer. Could you try asking again?", maps
        contents.append(candidate.content)
        calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
        if not calls:
            return _text_of(candidate.content) or "Sorry, I couldn't come up with an answer.", maps

        responses = []
        for call in calls:
            outcome = call_function(call.name, dict(call.args or {}), user_id, scratch)
            if outcome.get("ok") and isinstance(outcome.get("result"), dict) \
                    and outcome["result"].get("display") == "map":
                maps.append(outcome["result"])
            responses.append(types.Part.from_function_response(name=call.name, response=outcome))
        contents.append(types.Content(role="user", parts=responses))
    return "That took more steps than I expected. Could you tell me again what you'd like to do?", maps


# ---------------------------------------------------------------- map

_PIN_COLORS = {"green": "green", "yellow": "orange", "red": "red", "grey": "gray"}


def _render_map(result, key):
    import folium
    from streamlit_folium import st_folium

    programs = [p for p in result.get("universities", []) if p.get("coordinates")]
    if not programs:
        return
    fmap = folium.Map(location=[39.6, -8.0], zoom_start=6, tiles="OpenStreetMap")
    for p in programs:
        last = p.get("last_grade_200")
        popup = f"<b>{p['program_name']}</b><br>{p['institution_name']}<br>" \
                f"Last placed: {last if last else 'n/a'} / 200"
        folium.Marker(
            [p["coordinates"]["lat"], p["coordinates"]["lon"]],
            popup=folium.Popup(popup, max_width=280),
            tooltip=p["institution_name"],
            icon=folium.Icon(color=_PIN_COLORS.get(p.get("map_color"), "gray")),
        ).add_to(fmap)
    lats = [p["coordinates"]["lat"] for p in programs]
    lons = [p["coordinates"]["lon"] for p in programs]
    if len(programs) > 1:
        fmap.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(30, 30), max_zoom=9)
    else:
        fmap.location, fmap.options["zoom"] = [lats[0], lons[0]], 9
    st_folium(fmap, height=380, use_container_width=True, returned_objects=[], key=key)
    extra = result.get("without_map_pin")
    if extra:
        st.caption(f"{extra} program(s) have no map location.")


# ---------------------------------------------------------------- page

def _read_input(prompt):
    """(text, image parts) from st.chat_input, which is a plain string or an object with files."""
    if prompt is None:
        return None, []
    if isinstance(prompt, str):
        return prompt, []
    getter = prompt.get if hasattr(prompt, "get") else (lambda k, d=None: getattr(prompt, k, d))
    text = getter("text", "") or ""
    files = getter("files", []) or []
    images = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/png") for f in files]
    return text.strip(), images


def render_dashboard_chat():
    """The student chat page."""
    load_all()
    _init_state()
    user_id = get_user_id()
    guest = is_guest(user_id)

    st.header("Okay, now what?")

    api_key = get_gemini_api_key()
    if not api_key:
        st.error("The Gemini API key is missing. Add GOOGLE_API_KEY to the app's secrets.")
        return

    top_left, top_right = st.columns([3, 1])
    with top_right:
        if st.button("New chat", width="stretch"):
            _reset_chat()
            st.rerun()
    with top_left:
        if guest:
            st.caption("You're a guest, so you can try everything, but nothing is saved. Log in to keep your results.")
        else:
            past = database.get_conversations(user_id)
            if past:
                with st.expander("Past chats"):
                    for conv in past[:15]:
                        if st.button(conv["title"] or "Chat", key=f"conv_{conv['id']}", width="stretch"):
                            _load_conversation(user_id, conv["id"])
                            st.rerun()

    starters = st.empty()
    if not st.session_state.chat_messages:
      with starters.container():
        st.markdown("Tell me what's on your mind, or pick a place to start. You can also attach a screenshot of your grades.")
        columns = st.columns(2)
        for i, (label, text) in enumerate(STARTERS):
            if columns[i % 2].button(label, key=f"starter_{i}", width="stretch"):
                st.session_state.chat_pending = text
                st.rerun()

    for i, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for j, result in enumerate(msg.get("maps", [])):
                _render_map(result, key=f"map_{i}_{j}")

    try:
        prompt = st.chat_input(PLACEHOLDER, accept_file=True, file_type=IMAGE_TYPES)
    except TypeError:  # older Streamlit without file attachments in the chat box
        prompt = st.chat_input(PLACEHOLDER)

    text, images = _read_input(prompt)
    pending = st.session_state.pop("chat_pending", None)
    if pending and not text:
        text = pending
    if not text and not images:
        return
    if not text:
        text = "Here is a screenshot of my grades."
    starters.empty()

    shown = text + (f"\n\n*(attached {len(images)} image{'s' if len(images) > 1 else ''})*" if images else "")
    st.session_state.chat_messages.append({"role": "user", "content": shown, "maps": []})
    base = len(st.session_state.chat_contents)
    st.session_state.chat_contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=text)] + images))
    with st.chat_message("user"):
        st.markdown(shown)

    if not guest:
        if st.session_state.chat_conversation_id is None:
            st.session_state.chat_conversation_id = database.create_conversation(user_id, text[:60])
        if st.session_state.chat_conversation_id:
            database.add_message(st.session_state.chat_conversation_id, user_id, "user", shown)

    client = genai.Client(api_key=api_key)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, maps = run_turn(client, st.session_state.chat_contents, user_id, st.session_state.chat_scratch)
            except Exception as e:  # keep the conversation usable after a failed request
                answer, maps = "Something went wrong reaching the AI. Please try again in a moment.", []
                print(f"Chat error: {type(e).__name__}: {e}")
                del st.session_state.chat_contents[base:]  # forget the failed turn so the next one starts cleanly
        st.markdown(answer)
        for j, result in enumerate(maps):
            _render_map(result, key=f"map_new_{len(st.session_state.chat_messages)}_{j}")

    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "maps": maps})
    if not guest and st.session_state.chat_conversation_id:
        database.add_message(st.session_state.chat_conversation_id, user_id, "assistant", answer)
