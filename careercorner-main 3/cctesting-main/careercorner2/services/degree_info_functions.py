"""What a degree is about (objectives, content, career outlook), from the universities' own pages.

Only some universities are collected (see utils/degree_info.py). For any other program the answer says so
and gives the institution's website, so the assistant never describes a curriculum from its own knowledge.
"""
from services.chat_functions import chat_function
from services.university_functions import find_program
from utils.degree_info import (covered_universities, institution_site, record_for, search)

@chat_function(
    "search_degree_info",
    "What a degree is about: objectives, what is studied, career outlook, from the university's own page, with "
    "the source link. Only some universities are covered; for the others it returns not_covered and the school's "
    "website, and you must NOT describe the content from your own knowledge: give the link instead. "
    "Give course_code and institution_name (exactly as returned by search_universities) for one program, or only "
    "a question to look across all covered degrees (for example 'degrees about robotics').",
    {"properties": {
        "question": {"type": "string", "description": "What the student wants to know. WRITE IT IN PORTUGUESE (the pages are in Portuguese), with the key words of the topic"},
        "course_code": {"type": "string", "description": "DGES course code from search_universities"},
        "institution_name": {"type": "string", "description": "Institution name from search_universities"}},
     "required": ["question"]},
)
def search_degree_info(user_id, question, course_code=None, institution_name=None):
    coverage = "Covered universities: " + (", ".join(covered_universities()) or "none yet")
    if course_code and institution_name:
        row = find_program(course_code, institution_name)
        name = institution_name if row is None else str(row.get("institution_name"))
        record = record_for(course_code, name)
        if record is None:
            return {"covered": False, "institution_name": name, "institution_website": institution_site(name),
                    "message": "No degree description was collected for this program. Do not describe it from "
                               "memory. Point the student to the website and say what you do know from DGES "
                               "(cut-offs, entrance exams).", "coverage": coverage}
        return {"covered": True, "passages": search(question, record), "coverage": coverage}
    passages = search(question)
    if not passages:
        return {"covered": True, "passages": [], "message": "Nothing matched in the covered degrees.", "coverage": coverage}
    return {"covered": True, "passages": passages, "coverage": coverage,
            "note": "Only covered universities appear here; other universities may offer similar degrees."}
