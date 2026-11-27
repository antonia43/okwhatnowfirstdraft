"""Small pure helpers for the chat and Saved pages (no Streamlit, so they are easy to test)."""

TAGS = ("Grades", "Quiz", "Universities", "Resources")
GENERAL = "General"
SEPARATOR = " · "

_TAG_OF_FUNCTION = {
    "calculate_admission_grade": "Grades", "save_grades": "Grades", "get_saved_grades": "Grades",
    "check_chances_for_degree": "Grades", "compare_saved_universities": "Grades", "read_uploaded_grades": "Grades",
    "sector_quiz": "Quiz", "save_sector_result": "Quiz", "degree_quiz": "Quiz", "save_degree_results": "Quiz",
    "search_universities": "Universities", "save_university": "Universities",
    "get_saved_universities": "Universities", "remove_saved_university": "Universities",
    "find_study_resources": "Resources", "get_exam_papers": "Resources", "get_scholarships": "Resources",
}
CHANCE_COLORS = {"green": "#2e9e4f", "yellow": "#e0b000", "red": "#d64545", "grey": "#8a8a8a"}


def conversation_tag(events, current=None):
    """The chat's topic. A chat keeps the first topic it got; a new chat starts as General."""
    if current and current != GENERAL:
        return current
    for event in events or []:
        tag = _TAG_OF_FUNCTION.get(event.get("name"))
        if tag:
            return tag
    return GENERAL


def make_title(tag, first_message, limit=48):
    text = " ".join(str(first_message or "").split()) or "New chat"
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return f"{tag}{SEPARATOR}{text}"


def split_title(title):
    """(tag, text) from a saved title; chats made before this had no tag and count as General."""
    title = str(title or "")
    head, sep, rest = title.partition(SEPARATOR)
    if sep and head in TAGS + (GENERAL,):
        return head, rest
    return GENERAL, title or "New chat"


def group_conversations(conversations):
    """{tag: [conversation, ...]} in a fixed order, newest first inside each group (input order is kept)."""
    groups = {tag: [] for tag in TAGS + (GENERAL,)}
    for conv in conversations or []:
        tag, text = split_title(conv.get("title"))
        groups[tag].append({**conv, "tag": tag, "text": text})
    return {tag: items for tag, items in groups.items() if items}


def map_points(result):
    """Universities of a search_universities result that can be pinned: [{...program, 'lat', 'lon', 'hex'}]."""
    points = []
    for uni in (result or {}).get("universities", []):
        coords = uni.get("coordinates") or {}
        if coords.get("lat") is None or coords.get("lon") is None:
            continue
        points.append({**uni, "lat": float(coords["lat"]), "lon": float(coords["lon"]),
                       "hex": CHANCE_COLORS.get(uni.get("map_color"), CHANCE_COLORS["grey"])})
    return points


def pin_label(uni):
    """Tooltip text that identifies a pin when it is clicked."""
    return f"{uni.get('institution_name', '')} — {uni.get('program_name', '')}"


def grade_text(uni):
    last = uni.get("last_grade_200")
    return f"{last:.1f}/200 ({last / 10:.2f}/20)" if last else "no last grade available"


CHANCE_WORDS = {"safe": "Safe", "target": "Target", "reach": "Reach", "unknown": ""}


# ---- sources shown under an answer --------------------------------------------------

DGES_SITE = "https://www.dges.gov.pt"
_DGES_FUNCTIONS = {"search_universities", "check_chances_for_degree", "check_program_requirements",
                   "find_safer_alternatives", "compare_saved_universities", "get_saved_universities"}
_GRADE_FUNCTIONS = {"calculate_admission_grade", "read_uploaded_grades", "get_saved_grades"}
_LINK_FUNCTIONS = {"find_study_resources", "get_exam_papers", "get_scholarships"}
_DGES_LABEL = {"check_program_requirements": "DGES course page, 2026 applications"}
MAX_SOURCES = 4


def sources_for(events):
    """What the answer was based on: [{'label', 'url' (may be '')}], in the order the functions ran.

    Only functions that ran successfully count, so the line under an answer never names a source
    the answer did not use. Degree text names the university page it came from.
    """
    out, seen = [], set()

    def add(label, url=""):
        if (label, url) not in seen and len(out) < MAX_SOURCES:
            seen.add((label, url))
            out.append({"label": label, "url": url})

    for event in events or []:
        if event.get("sources"):  # a stored copy from an earlier session
            for item in event["sources"]:
                add(item.get("label", ""), item.get("url", ""))
            continue
        if not event.get("ok"):
            continue
        name, result = event.get("name"), event.get("result") or {}
        if name in _DGES_FUNCTIONS:
            add(_DGES_LABEL.get(name, "DGES 2026 first-phase results"), DGES_SITE)
        elif name in _GRADE_FUNCTIONS:
            add("Your grades, as entered")
        elif name == "search_degree_info":
            for passage in result.get("passages") or []:
                if passage.get("source_url"):
                    add(f"{passage.get('school') or 'University'} degree page", passage["source_url"])
        elif name in _LINK_FUNCTIONS:
            links = [x for x in (result.get("sources") or []) if isinstance(x, dict) and x.get("url")]
            for x in links[:2]:
                add(x.get("title") or x["url"], x["url"])
            if not links:
                add({"find_study_resources": "Web search for study resources", "get_exam_papers": "IAVE exam archive",
                     "get_scholarships": "Scholarship pages (DGES, FCT, Erasmus+)"}[name])
    return out


def sources_line(sources):
    """The caption text: 'Source: [DGES 2026 first-phase results](https://...) · Your grades, as entered'."""
    parts = [f"[{s['label']}]({s['url']})" if s.get("url") else s["label"] for s in sources]
    if not parts:
        return ""
    return ("Source: " if len(parts) == 1 else "Sources: ") + " · ".join(parts)


def follow_up_buttons(events):
    """Buttons for the last answer: [(label, shown text, hidden detail)]. Only after a program check that was not safe."""
    for event in reversed(events or []):
        result = event.get("result") or {}
        if event.get("ok") and event.get("name") == "check_program_requirements" \
                and result.get("chance") in ("reach", "target", "not_eligible") and "admission_grade_200" in result:
            args = event.get("args") or {}
            program = f"{result.get('program_name')} at {result.get('institution_name')}"
            detail = f"[course_code={args.get('course_code')}; institution_name={args.get('institution_name')}]"
            buttons = [("What if I raise my exam grades?", f"What if I raise my exam grades by 10 points (1 out of 20) for {program}?", detail)]
            buttons.append(("Show safer alternatives", f"Show me similar programs where I would be safer than {program}.", detail))
            return buttons
    return []
