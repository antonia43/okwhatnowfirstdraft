"""The chat engine: one conversation with Gemini that can call every ability.

run_turn() takes the student's message, lets Gemini call functions from the registry
(services/chat_functions.py) as often as it needs, and returns the final answer plus
a record of what was called. It never touches Streamlit, so it can be tested with a
stand-in model. GeminiAdapter is the real model; tests pass a fake with the same
generate() method.
"""
import json

from services import chat_functions

MODEL_NAME = "gemini-2.5-flash"
MAX_ROUNDS = 6
TEMPERATURE = 0.4

OPENING_MESSAGE = (
    "Hi! I'm here to help you figure out what to study in Portugal and which universities fit you.\n\n"
    "What's your main question right now? You can ask about degrees, grades and your chances, "
    "universities, or study resources. If you're not sure where to start, just tell me what you "
    "already know about yourself."
)

SYSTEM_PROMPT = """You are "Okay, now what?", a friendly study advisor chatting with students in Portugal who are deciding what to study after school and where.

WHAT YOU KNOW
- Facts about Portuguese degrees, universities, last-placed grades and chances come ONLY from your functions, which use the official DGES data. Never invent a grade, a university, a deadline or a number. If a function finds nothing, say so and suggest another search.
- You do not know the student yet. Learn what they already know about themselves and meet them there. Do not push a fixed order: a student may know their field but not their grades, or have grades but no idea what to study.

WHAT YOU CAN DO (all optional, in any order, only when it helps)
- Career Discovery quiz (sector_quiz): for a student who does not know what kind of work or field fits them. 10 playful questions.
- Degree quiz (degree_quiz): for a student who names a field and wants to narrow down to 3 degrees.
- Grades: calculate the admission average (calculate_admission_grade), read a screenshot or PDF of a transcript (read_uploaded_grades), check chances for a degree (check_chances_for_degree), compare saved universities (compare_saved_universities).
- Universities: search_universities shows programs on a map with colours (green = safe, yellow = target, red = reach). Save, list and remove with save_university, get_saved_universities, remove_saved_university.
- Study resources, exam papers and scholarships: find_study_resources, get_exam_papers, get_scholarships.
- Profile: get_student_profile tells you what is already known. Use it early for a signed-in student so you do not repeat questions. update_student_profile remembers details the student shares (school year, track, interests, preferred regions).

HOW TO RUN A CONVERSATION
- Start from the student's question. Ask at most ONE question at a time, only what you need.
- If the student does not know where to start, offer the options in one or two short sentences and let them choose. Do not list every ability.
- Quizzes: ask each question exactly as the function returns it, then call the function with the student's answer. Do not answer for them. When a quiz finishes, summarise the result in a few sentences and offer to save it.
- Saving: only save after the student agrees. Signed-in students can save quiz results, grades and universities. For a guest, saving is not possible: say once, kindly, that they need to log in or register to keep things, and carry on helping.
- Grades: school subject grades are 0-20. National exams, the admission average (CIF) and DGES last-placed grades are 0-200. Show 0-200 and its 0-20 equivalent (divide by 10) when talking about cut-offs.
- When the student uploads a grades file, call read_uploaded_grades, show what was read as a short list, and ask them to check it. Only calculate or save after they confirm or correct it. A guest's grades are not stored: pass all the grades again, or the grade in 0-200, when you call other functions.
- Chances: green means the grade is clearly above last year's last-placed grade, yellow means within 10 points either way, red means more than 10 points below. Last year's cut-off does not guarantee this year's. Say that plainly.
- When search_universities returns programs, the app shows the map itself. Do not repeat the whole list. Point out two or three interesting ones in words and say they can save any from the map.
- If a function returns an error, explain it simply and offer another way. Never show raw JSON, function names or error codes to the student.

STYLE
- Warm, clear and brief. Short paragraphs; a short list only when comparing options. Plain language for teenagers. No emoji unless the student uses them.
- Reply in the language the student writes in (Portuguese or English).
- Stay on studies and careers. For anything else, say you can't help with that here.
- Only Portugal is supported for now. If asked about studying abroad, say that international options are coming later.
"""


def declarations():
    """Function declarations for every registered ability."""
    chat_functions.load_all()
    return chat_functions.get_declarations()


def _plain(value):
    """Turn SDK containers (protobuf maps, etc.) into plain JSON-friendly Python."""
    return json.loads(json.dumps(value, default=lambda o: dict(o) if hasattr(o, "items") else list(o)))


def api_declaration(decl):
    """A declaration in the shape the Gemini API accepts: it refuses an object schema with no properties."""
    out = {"name": decl["name"], "description": decl["description"]}
    params = dict(decl.get("parameters") or {})
    if params.get("properties"):
        if not params.get("required"):
            params.pop("required", None)
        out["parameters"] = params
    return out


class GeminiAdapter:
    """The real model. generate() takes neutral messages and returns text, calls and the raw reply."""

    def __init__(self, api_key, model=MODEL_NAME):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _contents(self, messages):
        from google.genai import types

        out = []
        for m in messages:
            if "raw" in m:
                out.append(m["raw"])
                continue
            parts = []
            for p in m["parts"]:
                if "text" in p:
                    parts.append(types.Part(text=p["text"]))
                elif "image" in p:
                    parts.append(types.Part.from_bytes(data=p["image"]["bytes"], mime_type=p["image"]["mime"]))
                elif "function_call" in p:
                    parts.append(types.Part.from_function_call(name=p["function_call"]["name"], args=p["function_call"]["args"]))
                elif "function_response" in p:
                    fr = p["function_response"]
                    parts.append(types.Part.from_function_response(name=fr["name"], response=fr["response"]))
            out.append(types.Content(role=m["role"], parts=parts))
        return out

    def generate(self, messages, system_instruction, function_declarations):
        from google.genai import types

        tool = types.Tool(function_declarations=[types.FunctionDeclaration(**api_declaration(d)) for d in function_declarations])
        config = types.GenerateContentConfig(
            system_instruction=system_instruction, tools=[tool], temperature=TEMPERATURE,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        response = self.client.models.generate_content(
            model=self.model, contents=self._contents(messages), config=config)
        content = response.candidates[0].content if response.candidates else None
        calls = [{"name": c.name, "args": _plain(dict(c.args or {}))} for c in (response.function_calls or [])]
        text = "".join(p.text for p in (content.parts if content else []) if getattr(p, "text", None) and not getattr(p, "thought", False))
        return {"text": text.strip(), "calls": calls, "raw": content}


def run_turn(adapter, history, user_text, user_id, session, image=None, max_rounds=MAX_ROUNDS):
    """One student message in, one answer out.

    history : earlier turns as [{"role": "user" | "assistant", "content": str}]
    image   : optional {"bytes": ..., "mime": ...}. It is also stored in session["upload"] so the
              grades functions can read it.
    Returns {"text": str, "events": [{"name", "args", "ok", "result"|"error"}]}.
    """
    if image:
        session["upload"] = {"bytes": image["bytes"], "mime": image["mime"]}
    messages = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in history if m.get("content")]
    first = [{"text": user_text or "(sent a file)"}]
    if image:
        first.append({"text": "[The student attached a file. Use read_uploaded_grades if it is a grades transcript.]"})
    messages.append({"role": "user", "parts": first})

    system = SYSTEM_PROMPT
    if chat_functions.is_guest(user_id):
        system += "\nThis student is a GUEST: nothing can be saved. Do not call functions that save."
    decls = declarations()
    events = []
    for _ in range(max_rounds):
        reply = adapter.generate(messages, system, decls)
        if not reply["calls"]:
            return {"text": reply["text"] or "Sorry, I didn't catch that. Could you say it another way?", "events": events}
        messages.append({"raw": reply["raw"]} if reply.get("raw") is not None else
                        {"role": "model", "parts": [{"function_call": c} for c in reply["calls"]]})
        responses = []
        for call in reply["calls"]:
            outcome = chat_functions.call_function(call["name"], call["args"], user_id, session)
            events.append({"name": call["name"], "args": call["args"], **outcome})
            responses.append({"function_response": {"name": call["name"], "response": outcome}})
        messages.append({"role": "user", "parts": responses})
    return {"text": "I got a bit tangled up on that one. Could you try asking again, maybe in smaller steps?", "events": events}
