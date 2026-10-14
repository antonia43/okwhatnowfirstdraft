"""Registry and dispatcher for the abilities the chat can use.

Every ability is a plain Python function registered here with a name, a
description and typed parameters (the shape Gemini function calling needs).
The chat never runs a function directly. It goes through call_function, which:
- always supplies the signed-in user's id itself (the model cannot choose it),
- refuses functions that save data when the user is a guest,
- turns any error into a message the model can explain, instead of a crash.

Handlers have the form handler(user_id, **arguments) and return something
JSON-friendly. Abilities are independent: none needs another to have run first.
"""
import json
from dataclasses import dataclass
from typing import Callable

REGISTRY = {}


@dataclass
class ChatFunction:
    name: str
    description: str
    parameters: dict
    handler: Callable
    saves: bool = False  # writes to the student's account, so not for guests
    uses_session: bool = False  # gets the chat's scratch space (e.g. quiz progress) as session=


def chat_function(name, description, parameters=None, saves=False, uses_session=False):
    """Register a function with the chat."""
    schema = {"type": "object", "properties": {}, "required": []}
    schema.update(parameters or {})

    def decorator(handler):
        if name in REGISTRY:
            raise ValueError(f"Chat function '{name}' is already registered")
        REGISTRY[name] = ChatFunction(name, description, schema, handler, saves, uses_session)
        return handler

    return decorator


def is_guest(user_id):
    return not user_id or str(user_id).startswith("guest-")


def get_declarations(names=None):
    """Function declarations to hand to Gemini (all functions, or just names)."""
    functions = REGISTRY.values() if names is None else [REGISTRY[n] for n in names]
    return [
        {"name": f.name, "description": f.description, "parameters": f.parameters}
        for f in functions
    ]


def call_function(name, arguments, user_id, session=None):
    """Run a registered function for this user. Always returns a dict with 'ok'.

    session is the chat's scratch dict (kept for the length of the conversation);
    functions that need to remember something between turns, like a quiz, use it.
    """
    function = REGISTRY.get(name)
    if function is None:
        return {"ok": False, "error": f"Unknown function '{name}'."}
    if function.saves and is_guest(user_id):
        return {
            "ok": False,
            "error": "Guests can't save anything. Ask the student to log in or register to save this.",
        }

    arguments = dict(arguments or {})
    arguments.pop("user_id", None)  # never trust an id that came from the model
    missing = [p for p in function.parameters.get("required", []) if arguments.get(p) is None]
    if missing:
        return {"ok": False, "error": f"Missing required argument(s): {', '.join(missing)}."}
    allowed = set(function.parameters.get("properties", {}))
    arguments = {k: v for k, v in arguments.items() if k in allowed}

    try:
        if function.uses_session:
            arguments["session"] = session if session is not None else {}
        result = function.handler(user_id, **arguments)
        return {"ok": True, "result": json.loads(json.dumps(result, default=str))}
    except Exception as e:  # the model explains the problem to the student
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def load_all():
    """Import every module that registers functions."""
    from services import grade_functions, quiz_functions, university_functions  # noqa: F401
