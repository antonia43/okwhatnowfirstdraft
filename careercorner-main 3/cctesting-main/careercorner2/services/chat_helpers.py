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
