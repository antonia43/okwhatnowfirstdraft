"""Resource abilities: exam papers, scholarships and the Google-search helpers
(study resources, career options, salaries, city guides).

The links and the search prompts are the same as the old Resources page
(services/tools.py). Only the web search needs Gemini; it is loaded when used.
"""
from services.chat_functions import chat_function

EXAM_PAPER_LINKS = [
    {"name": "IAVE current national exams", "description": "The latest national exams",
     "url": "https://iave.pt/provas-e-exames/provas-e-exames/provas-e-exames-finais-nacionais-es/"},
    {"name": "IAVE exam archive", "description": "Past papers from all previous years",
     "url": "https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/"},
]

SCHOLARSHIPS = [
    {"name": "DGES Scholarships", "description": "Portuguese government scholarships for higher education",
     "url": "https://www.dges.gov.pt/pt/pagina/bolsas-de-estudo"},
    {"name": "FCT Research Grants", "description": "Funding for research and postgraduate studies",
     "url": "https://www.fct.pt/apoios/bolsas/"},
    {"name": "Erasmus+ Mobility", "description": "Study abroad opportunities in Europe",
     "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students"},
]

_tools = None  # tests put a fake here


def _search_tools():
    if _tools is not None:
        return _tools
    from services import tools

    return tools


def _search(function_name, *args):
    """Run one of the Google-search helpers and return {answer, sources}."""
    result = getattr(_search_tools(), function_name)(*args)
    if not result.get("success"):
        raise RuntimeError(result.get("error") or "The web search failed")
    return {"answer": result["answer"], "sources": result.get("sources", [])}


def _required(value, what):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"Please tell me {what}.")
    return value


@chat_function(
    "get_exam_papers",
    "Links to the official IAVE national exam papers, current year and the full archive of past years.",
)
def get_exam_papers(user_id):
    return {"links": EXAM_PAPER_LINKS, "tip": "Practising with past papers helps with exam technique."}


@chat_function(
    "get_scholarships",
    "Links to scholarships and financial aid: DGES, FCT and Erasmus+.",
)
def get_scholarships(user_id):
    return {"scholarships": SCHOLARSHIPS}


@chat_function(
    "find_study_resources",
    "Search the web for free study resources (courses, videos, practice sites, communities, guides) "
    "for any subject, with direct links.",
    {"properties": {"subject": {"type": "string", "description": "e.g. Python, Biology, Calculus"}},
     "required": ["subject"]},
)
def find_study_resources(user_id, subject):
    return _search("get_study_resources_web", _required(subject, "which subject to study"))


@chat_function(
    "explore_career_options",
    "Search the web for the career paths, job titles, seniority levels, salary ranges and industries "
    "that a degree leads to.",
    {"properties": {"degree": {"type": "string", "description": "The degree or course, e.g. Psychology"}},
     "required": ["degree"]},
)
def explore_career_options(user_id, degree):
    return _search("get_career_options", _required(degree, "which degree to look at"))


@chat_function(
    "find_salaries",
    "Search the web for entry, mid and senior salary ranges for a job title in a country (default Portugal).",
    {"properties": {"job_title": {"type": "string", "description": "e.g. Nurse, Software Engineer"},
                    "country": {"type": "string", "description": "Defaults to Portugal"}},
     "required": ["job_title"]},
)
def find_salaries(user_id, job_title, country="Portugal"):
    return _search("get_wage_info", _required(job_title, "which job title"), (country or "").strip() or "Portugal")


@chat_function(
    "get_city_guide",
    "Search the web for a student guide to any city: universities, cost of living, student life, transport, "
    "culture and practical information.",
    {"properties": {"city": {"type": "string", "description": "e.g. Porto"},
                    "country": {"type": "string", "description": "Optional, e.g. Portugal"}},
     "required": ["city"]},
)
def get_city_guide(user_id, city, country=""):
    return _search("get_city_guide", _required(city, "which city"), (country or "").strip())
