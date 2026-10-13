# Career Corner - Architecture Documentation

---

## Problem Statement & Project Overview 

Career Corner is an AI-powered career guidance platform designed for high school students navigating university admissions and professionals seeking job market advancement. Students struggle with vague psychotechnical tests, scattered degree information, and disconnected final grade calculations, while professionals face challenges tailoring CVs and preparing for interviews without clear skill path mappings. As former high school students and aspiring data scientists, the creators of Career Corner aimed to bridge these gaps by combining adaptive conversational AI, real Portuguese education data (DGES catalogs, IAVE exams, CIF formulas), built-in research tools, and practical features into dual student/professional dashboards, delivering personalized sector matches (i.e. Healthcare), university finders with interactive maps, CV parsing, mock interviews, and final reports that connect interests, grades, and actionable career paths far beyond generic advice.

---

## Architecture Decisions

### Why Streamlit?

Streamlit was used for the frontend framework because it was taught in class and therefore there was higher familiarity with it, allowing us to deploy our application faster through a cloud, without the need to spend extra valuable time learning a different frontend option. This made it so that we could focus our time working on the concrete app features.
Although streamlit is very convenient, since it is natively integrated to python and has built-in session management, the UI customization is very limited. We used CSS styling (styles.py) to bypass some of the limitations, allowing for some more personalization and colorfulness.


### Why Google Gemini?
Decision: Google Gemini 2.5 Flash as the primary LLM.
For similar reasons as stated above, Google Gemini was the LLM preferred since it was used in class and differentiates itself from other LLMs like OpenAI GPT-4 (cost prohibitive), Claude (lower free tier limits), by a very generous free tier. It also handles both text and images so we could process CVs and grade reports (images, pdfs), and its large context window let us send entire documents to the AI without complex RAG setups.


### Why No RAG/Vector Database?

Following the above rationale, Google Gemini has a large context window, so we opted for direct context injection instead of RAG, mainly since the files our application would ingest (Cvs and grades) fit within Gemini's 200K context window. Gemini's architecture is also simpler, so there are fewer failure points. Additionally, there is no semantic search requirement (students ask specific questions, not "find similar")


### Why Langfuse?

We used Langfuse because it was taught in class and the free tier worked for our project. Langfuse was used to track AI generation so we could understand the functioning behind the AI and check if everything was working correctly. We logged user thumbs-up/down feedback to improve prompts over time, but later removed it from the final deployment version.

### Key Design Decisions

1. **Dual Dashboard Architecture:** Separate `student_dashboard.py` vs `professional_dashboard.py` prevents feature overload while sharing common services/database. Onboarding gates confirm user type before access.

2. **LangfuseGeminiWrapper Pattern:** Single wrapper handles most of Gemini calls with automatic tracing (user_id, session_id, temperature, metadata). Raw Gemini client used only for function calling in resources. Graceful fallback if Langfuse unavailable.

3. **Database-First Persistence:** SQLite tempdir stores everything (reports, CVs, universities) enabling dropdown selection in chats ("Select CV: My Resume - 2025-12-21"). No data loss across Streamlit reruns/sessions.

4. **One File Per Feature:** 14 UI files (`student_career_quiz.py`, `cv_builder.py`, etc.) = modular development, each file self-contained with session_state management.

5. **5-Question Chat Routing:** Dashboard chatbots (`student_chat.py`, `professional_chat.py`) ask 5 natural questions before recommending tools ("Career Quiz would suit you best because..."). Prevents premature tool spam, builds context and helps users navigate the app with ease.

6. **Streamlit-Native Workflows:** No FastAPI/React. Session_state + `st.rerun()` handles complex multi-step flows (10Q quizzes, 10Q interviews). Progress bars + back/next navigation prevent user frustration.

7. **Zero External Dependencies:** SQLite tempdir + standard library (json/re/os/datetime) = instant deployment. Only 6 pip packages needed. Works offline except Gemini API calls.

**Why This Works:** All files are production-ready, so zero configurations are needed to deploy to Streamlit Cloud. The project relies only on a small, well-defined set of Python dependencies and the built-in SQLite database, which means there is no need to provision external services, containers, or complex infrastructure. The folder structure is clear and consistent, with each major feature living in its own file, so the application can be understood and modified quickly even by someone new joining the project.

The use of a single Gemini wrapper with integrated tracing ensures that every AI interaction is automatically logged with the same pattern, instead of each page having its own fragile API logic. This makes it much easier to debug quizzes, CV analysis, or interview feedback without hunting through different files or logging systems. Observability becomes a built-in part of the architecture rather than an afterthought, so prompt iterations and quality improvements can be done with confidence.

Because each feature is encapsulated in its own Streamlit page file, the codebase scales very naturally: new tools can be added as new files, and existing ones can be refactored in isolation. At the same time, the shared services and database utilities keep repeated logic in one place, so the overall complexity stays low. The result is a system that is modular enough to support team development—different people can own different feature files—but still simple enough that a single maintainer can understand, debug, and extend the whole application without feeling overwhelmed.


---

## Technology Stack

### Backend
- Language: Python 3.13
- LLM Provider: Google Gemini 2.5 Flash (used for all features and tools)
- Database: SQLite (lightweight, file-based) to store user reports and saved universities in the temp directory so data persisted across Streamlit sessions
- Authentication: Custom implementation with werkzeug password hashing


### Frontend
- Framework: Streamlit 1.40+
- UI Components: Native Streamlit widgets

Streamlit handled all UI components including tabs, chat interfaces, progress bars, and sliders. Custom CSS was used to implement DM Sans typography, button hover and text animations, and a consistent yellow and green design across both student and professional dashboards.


### Stack Overview

- Package Manager: pip with virtual environment (venv) managing dependencies including streamlit 1.40+, google.genai, langfuse v3.11.1, reportlab, werkzeug-security, doc2text, PyPDF2, folium (streamlit folium).
- Version Control: Git with GitHub repository following modular folder structure (pages/services/utils)
- Environment Management: .env files for local development with dotenv, Streamlit Cloud secrets for production (GOOGLE_API_KEY, LANGFUSE credentials, GOOGLE_CLIENT(ID/SECRET) optional, for Google OAuth login feature)
- Database: SQLite in tempdir with automatic init_database() call handling users, professional_reports, saved_universities, user_cvs tables
- Deployment: Streamlit Cloud with automatic GitHub integration, zero-downtime deploys from main branch
- Debugging: Langfuse dashboard for tracing AI generations
- File Organization: 24 Python files structured as pages/ (14 UI), services/ (5), utils/ (2), scripts(1), top-level helpers (styles.py, zapp.py)
- Static Assets: data/ folder with images for CSS backgrounds and branding
- Documentation: root README.md file with project details and instructions, docs/ folder with ARCHITECTURE.md (architecture decisions and technical choices) and TOOLS.md (documenting each tool)


### AI & Monitoring

- **LLM Provider:** Google Gemini (`gemini-2.5-flash`)
- **Observability:** Langfuse v3.11.1
- **Function Calling:** 8 built-in tools + 9 custom function calling tools

### Function Calling and Built-In Tools
#### Built-In Tools (7)
Built-in tools use Google's native capabilities (Google Search & URL Context) to retrieve real-time web data:

1. **get_study_resources_web** - Finds free online courses, video tutorials, practice websites, and community resources for any subject
2. **get_career_options** - Discovers career paths, job titles, and salary ranges for specific degrees
3. **get_wage_info** - Retrieves salary information by experience level (entry/mid/senior) for job titles in any country
4. **get_job_search_results** - Returns direct links to job postings from LinkedIn, Indeed, Glassdoor, and company career pages
5. **get_course_recommendations** - Finds online courses from Coursera, Udemy, edX, LinkedIn Learning, and YouTube for specific skills
6. **get_linkedin_profile_optimization** - Provides headline options, About section rewrites, skill recommendations, and profile improvement tips
7. **get_company_research** - Delivers company culture, reviews, news, benefits, and salary information

#### Custom Function Calling Tools (4)
Function calling tools access user-specific data from Career Corner's SQLite database:

**Professional Tools (4):**
1. **analyze_skill_gaps** - Compares current CV skills against target role requirements and identifies missing competencies
2. **get_career_roadmap** - Generates phased career roadmaps (6 months / 1 year / 2 years) based on stored profile data
3. **compare_career_paths** - Compares two careers based on suitability for users in relation to their data
4. **calculate_career_readiness** - Tells user how ready they are (on a scale of 0-100%) for a certain career based on their data


#### Tool Usage & Monitoring

Langfuse wraps all Gemini calls to track prompts, responses, and token usage. Function calls in `resources.py` (professional resources) are monitored using the `@observe` decorator rather than wrapped directly.

**Distribution:**
- **Professional Resources:** 4 custom function calling tools (career support chat) + 5 built-in tools (4 on main page: job search, courses, LinkedIn optimizer, company research + 1 in CV Builder cover letter page: fetch_job_description_from_url)

All function calling tools implement 3-attempt retry logic for resilience against database locks and transient errors.

For detailed information about the tools, please refer to [TOOLS.md](docs/TOOLS.md)


### Deployment
- Platform: Streamlit Cloud
- Environment Management: .env files (local), Streamlit secrets (production)
We deployed to Streamlit Cloud which worked perfectly for our GitHub based workflow. SQLite tempdir was used for persistence without external databases. Environment variables were used to secure our API keys in Streamlit Secrets.



---

## System Architecture

Career Corner follows a modular layered architecture with clear separation of concerns. The application routes users between student and professional dashboards (`student_dashboard.py` vs `professional_dashboard.py`) based on account type, with each dashboard providing access to specialized tools.

### High-Level Overview

**Student Pipeline:**
- `student_career_quiz.py` - 10-question adaptive personality assessment
- `degree_picker.py` - AI-guided degree recommendations via yes/no questions
- `grades_analysis.py` - CIF calculator with multimodal grade extraction
- `university_finder.py` - DGES database search with interactive maps
- `student_resources.py` - Quick search tools for students

**Professional Pipeline:**
- `cv_analysis.py` - Multimodal CV parser extracting structured JSON
- `career_growth_quiz.py` - CV-aware 12-question career assessment
- `interview_simulator.py` - Mock interviews with STAR method feedback
- `cv_builder.py` - 3-mode CV toolkit (build/tailor/cover letter)
- `resources.py` - Job search + course finder + AI support chat

**Shared Infrastructure:**
- `authentication.py` - User management (local + Google OAuth)
- `langfuse_helper.py` - LangfuseGeminiWrapper for AI observability
- `database.py` - SQLite operations across 4 tables
- `reports.py` - "My Reports" interface for saved data
- `styles.py` - Consistent CSS branding

---
```
careercorner2/
├── pages/ # User-facing pages
│ ├── career_growth_quiz.py
│ ├── cv_analysis.py
│ ├── cv_builder.py
│ ├── degree_picker.py
│ ├── grades_analysis.py
│ ├── interview_simulator.py
│ ├── professional_chat.py
│ ├── professional_dashboard.py
│ ├── resources.py
│ ├── student_career_quiz.py
│ ├── student_chat.py
│ ├── student_dashboard.py
│ ├── student_resources.py
│ └── university_finder.py
├── services/ # business logic + external integrations
│ ├── __init__.py
│ ├── authentication.py  # manual and Google Login/session helpers
│ ├── langfuse_helper.py  # Langfuse + Gemini wrappers
│ ├── professional_tools.py
│ └── tools.py
├── utils/ # shared helpers and data access
│ ├── __init__.py
│ ├── database.py
│ └── reports.py
├── scripts/ 
│ ├── __init__.py
│ └── build_dges_universities.py
├── data/ # static files
│ ├── bg1.png
│ ├── bg2.png
│ ├── careercornerlogo2.png
│ ├── careercornermini.png
│ ├── crumpledpaper2.jpg
│ ├── crumpledpaper3.avif
│ └── universities_2025_1f.csv
├── docs/
│ ├── ARCHITECTURE.md
│ └── TOOLS.md
├── config/
│   ├── __init__.py
│   ├── models.py
│   ├── prompts.py
│   └── schemas.py
├── zapp.py # Main Streamlit entry
└── styles.py # Custom CSS styling functions
├── README.md
├── requirements.txt
└── .env.example
```

### Component Breakdown
### Layer Structure

**Presentation Layer** (`zapp.py`, `pages/`)
14 modular UI files, one per feature: `student_career_quiz.py` (10Q adaptive quiz), `cv_analysis.py` (PDF parsing), `interview_simulator.py` (mock interviews), etc. Each handles its own session_state, progress bars, back/next navigation, and auto-save confirmations. Streamlit widgets (tabs, expanders, chat, sliders) create intuitive multi-step workflows.

**Service Layer** (`services/`)
`authentication.py` manages SQLite users + Google OAuth. `langfuse_helper.py` provides `LangfuseGeminiWrapper` class wrapping most of Gemini calls with v3 tracing (prompts, responses, tokens, user feedback). Centralized services prevent code duplication across 14 UI files.
Built-in tools defined in `tools.py` (for both students and professionals, as some tools work for both). Function calling tools defined in `student_tools.py` and `professional_tools.py`. Gemini function calling in professional resources' "career support chat" routes directly to these functions.

**Data Layer** (`utils/`)
`database.py` handles all SQLite operations across 4 tables (professional_reports, saved_universities, user_cvs, users) with tempdir persistence. `reports.py` renders tabbed My Reports with CV selectors and delete functionality. Zero external database configuration.

**Configuration Layer** (`config/`)
Centralizes all AI settings and prompts in three files: `models.py` (model names and temperature presets per feature), `prompts.py` (30+ reusable prompt templates grouped by module) and `schemas.py` (CV schemas, fallback questions, dropdown options).

**Styling Layer** (`styles.py`)
Centralized CSS with DM Sans typography, lime/yellow gradients, fade/slide animations, hover effects, and responsive components. `apply_custom_css()` called from `zapp.py` ensures consistent branding.

---

## Database Architecture

### Schema Overview

Career Corner uses SQLite with 5 tables optimized for dual dashboard architecture (student/professional). All complex data stored as JSON TEXT for flexibility, with tempdir persistence (`/tmp/career_corner.db`) ensuring zero-config deployment.

---

### Table Definitions

#### **users** (Authentication & Profile)
Core user table with local + OAuth support.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal user ID |
| `username` | TEXT | UNIQUE NOT NULL | Login identifier |
| `display_name` | TEXT | NOT NULL | UI display name |
| `email` | TEXT | UNIQUE NOT NULL | Email address |
| `password_hash` | TEXT | NOT NULL | Werkzeug bcrypt hash |
| `created_at` | TEXT | NOT NULL | Account creation timestamp |
| `remember_token` | TEXT | NULLABLE | Session persistence token |

**Relationships:** Foreign key parent for all other tables via `user_id`

---

#### **saved_universities** (Bookmarked Programs)
Stores favorite universities from University Finder with DGES admission data.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Record ID |
| `user_id` | TEXT | NOT NULL | References users |
| `institution_name` | TEXT | NOT NULL | University name |
| `program_name` | TEXT | NOT NULL | Degree program |
| `location` | TEXT | NULLABLE | City/region |
| `type` | TEXT | NULLABLE | Public/private |
| `grade_required` | TEXT | NULLABLE | Minimum CIF score |
| `duration` | TEXT | NULLABLE | Program length |
| `acceptance_rate` | TEXT | NULLABLE | Admission rate |
| `data` | TEXT | NOT NULL | Full university JSON |
| `saved_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Save timestamp |

**Unique Constraint:** `(user_id, institution_name, program_name)` prevents duplicates  
**Relationships:** References `users.username` via `user_id`  
**Usage:** University Finder save feature, Grades Analysis comparison, Student Resources chat

---

#### **user_quizzes** (Student Career Quiz)
One career quiz result per student (upsert pattern).

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `user_id` | TEXT | PRIMARY KEY | References users |
| `quiz_data` | TEXT | JSON | Quiz answers + sector results |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Quiz completion time |

**Design Pattern:** `ON CONFLICT(user_id) DO UPDATE` ensures single quiz per user  
**Relationships:** References `users.username` via `user_id`  
**Usage:** Career Discovery Quiz storage, Degree Picker sector selection  
**Note:** Partially deprecated - newer quizzes use `professional_reports` table

---

#### **user_cvs** (Parsed CV Data)
One parsed CV per professional user (upsert pattern).

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `user_id` | TEXT | PRIMARY KEY | References users |
| `parsed_data` | TEXT | JSON | Structured CV (skills, experience, education) |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last upload time |

**Design Pattern:** `ON CONFLICT(user_id) DO UPDATE` allows CV replacement  
**Relationships:** References `users.username` via `user_id`  
**Usage:** CV Analysis storage, Career Growth Quiz personalization, Interview Simulator context, CV Builder tailoring  
**JSON Schema:**
```json
{
  "skills": {"technical": ["Python", "SQL"], "soft": ["Leadership"]},
  "experience": [{"role": "Data Analyst", "company": "X", "years": 3}],
  "education": [{"degree": "BSc", "institution": "Y", "year": 2020}],
  "strengths": ["Problem-solving"],
  "gaps": ["Missing cloud certifications"]
}
```
# professional_reports – Multi-Purpose Report Storage

Flexible table storing all feature outputs for both students and professionals.

## Table Definition

| Column       | Type       | Constraints                    | Purpose                                      |
|-------------|------------|--------------------------------|----------------------------------------------|
| `id`        | INTEGER    | PRIMARY KEY AUTOINCREMENT      | Report ID                                    |
| `user_id`   | TEXT       | NOT NULL                       | References users                             |
| `report_type` | TEXT     | NOT NULL                       | Feature identifier (see below)               |
| `title`     | TEXT       | NOT NULL                       | User-facing report name                      |
| `content`   | TEXT       | NOT NULL                       | Markdown/text report                         |
| `cv_json`   | TEXT       | NULLABLE JSON                  | Metadata (sector matches, CV data, etc.)     |
| `created_at`| TIMESTAMP  | DEFAULT CURRENT_TIMESTAMP      | Generation timestamp                         |

**Relationships:** References `users.username` via `user_id`, allows multiple reports per user.  
**Usage:** My Reports interface, dropdown selectors in chat modes.

### Report Types

- `career_quiz` – Student career quiz results (stores sector percentages in `cv_json`)
- `career_growth` – Professional growth quiz results
- `cv_analysis` – CV feedback reports (stores parsed CV in `cv_json`)
- `interview_feedback` – Mock interview scores/feedback
- `cv_built` – Generated CVs from CV Builder
- `cover_letter` – Generated cover letters
- `degree_recommendations` – Degree Picker results
- `grades_analysis` – CIF calculation reports

---

## Database Functions

### University Management (6 functions)

```python
save_university(user_id, uni_data)           # Add bookmarked university
get_saved_universities(user_id)              # Retrieve all saved universities
remove_saved_university(user_id, name, prog) # Delete specific university
is_university_saved(user_id, name, prog)     # Check save status
get_saved_count(user_id)                     # Count saved universities
clear_all_saved(user_id)                     # Delete all saved universities
```

### CV Management (2 functions)

```python
save_user_cv(user_id, parsed_data)           # Store/update CV JSON (upsert)
load_user_cv(user_id)                        # Retrieve user's CV data
```

### Report Management (6 functions)

```python
save_report(user_id, type, title, content, cv_data)  # Store any report type
load_reports(user_id, report_type)                   # Retrieve reports by type
delete_report(report_id)                             # Remove specific report
save_quiz_result(user_id, quiz_data)                 # Legacy quiz storage
load_user_quiz(user_id)                              # Legacy quiz retrieval
load_career_quiz_metadata(user_id)                   # Extract sector data from latest quiz
```

---

## Design Patterns

### 1. Upsert Pattern (User-Scoped Single Records)

`user_cvs` and `user_quizzes` enforce one record per user using `ON CONFLICT DO UPDATE`:

```sql
INSERT INTO user_cvs (user_id, parsed_data)
VALUES (?, ?)
ON CONFLICT(user_id) DO UPDATE SET
    parsed_data = excluded.parsed_data,
    updated_at = CURRENT_TIMESTAMP;
```

**Why:** Students have one active career quiz, professionals have one active CV.

---

### 2. JSON Storage (Flexible Schema Evolution)

All complex data stored as JSON TEXT.

- **Benefits:** No schema migrations for CV structure changes, supports nested data.
- **Trade-off:** No SQL queries inside JSON (acceptable for report retrieval patterns).
- **Example:** CV skills array stored as  
  `{"technical": ["Python"], "soft": ["Leadership"]}`

---

### 3. Backward Compatibility (Safe Upgrades)

`load_reports()` checks for `cv_json` column before querying:

```python
c.execute("PRAGMA table_info(professional_reports)")
columns = [col[1] for col in c.fetchall()]
has_cv_json = 'cv_json' in columns
```

**Why:** Allows incremental deployments without breaking existing user data.

---

### 4. Tempdir Persistence (Zero-Config Deployment)

Database stored in `/tmp/career_corner.db`:

- **Benefits:** No connection strings, works on cloud hosting instantly.
- **Persistence:** Survives app reruns and restarts.
- **Scalability:** Sufficient for thousands of users with proper indexing.
- **Production Note:** For 10K+ users, migrate to PostgreSQL with same schema.

---

### 5. Auto-Initialization (Import-Time Setup)

`init_database()` called at module import:

```python
if __name__ == "__main__":
    init_database()

init_database()  # Runs when database.py is imported
```

**Why:** No manual setup needed – tables are created automatically on first run.

---

## Performance Considerations

### Current Indexes

- `saved_universities`: UNIQUE index on `(user_id, institution_name, program_name)`
- `user_quizzes`: PRIMARY KEY on `user_id`
- `user_cvs`: PRIMARY KEY on `user_id`

### Recommended Indexes for Scale (PostgreSQL)

```sql
CREATE INDEX idx_reports_user_type
  ON professional_reports(user_id, report_type);

CREATE INDEX idx_universities_user
  ON saved_universities(user_id);

CREATE INDEX idx_reports_created
  ON professional_reports(created_at DESC);
```

### Common Query Patterns

- **My Reports:**  
  `SELECT * FROM professional_reports WHERE user_id = ? AND report_type = ? ORDER BY created_at DESC;`
- **Saved Universities:**  
  `SELECT * FROM saved_universities WHERE user_id = ? ORDER BY saved_at DESC;`
- **Latest Quiz:**  
  `SELECT cv_json FROM professional_reports WHERE user_id = ? AND report_type = 'career_quiz' ORDER BY id DESC LIMIT 1;`

---

## Migration Strategy (Future Scalability)

If outgrowing SQLite (e.g., 10K+ concurrent users):

- **PostgreSQL Schema:** Use identical table definitions with minimal changes.
- **Connection Pool:** Replace `sqlite3.connect()` with a pooled Postgres client.
- **JSON Columns:** Switch TEXT to native `JSONB` for indexing inside JSON.
- **User ID Type:** Change TEXT to INTEGER foreign key with `ON DELETE CASCADE`.
- **Transactions:** Add explicit `BEGIN`/`COMMIT` for multi-table operations.

**Estimated Migration Time:** 2–3 days (schema is mostly compatible; main work is connection logic and JSON column types).



## File Overview and Responsibilities

| File | Purpose |
|------|---------|
| `zapp.py` | **Main Streamlit entry point** with student/professional dashboard routing and sidebar navigation |
| `styles.py` | **Custom CSS styling** with DM Sans fonts, lime/yellow gradients, animations, and responsive components |
| `langfuse_helper.py` | **LangfuseGeminiWrapper** for all Gemini calls with v3 tracing, user_id/session_id tracking, feedback logging) |
| `database.py` | **SQLite operations** for professional_reports (CV/quiz results), saved_universities, user_cvs tables with tempdir persistence |
| `reports.py` | **Tabbed My Reports interface** with CV selectors, delete buttons, student/pro separate tabs |
| `authentication.py` | **Local login/register** with Werkzeug password hashing and session management |
| `student_dashboard.py` | **Student tool routing** (Career Quiz, Grades, Degree Picker, University Finder, Resources) |
| `professional_dashboard.py` | **Professional tool routing** (CV Analysis, Career Growth, Interview Prep, CV Builder, Your Next Steps) |
| `student_career_quiz.py` | **Adaptive 10Q career quiz** → sector matches (Healthcare 60%) + degree paths, auto-saves |
| `career_growth_quiz.py` | **CV-aware professional quiz** (Experience + Soft Skills phases) → growth paths, uses parsed CV JSON |
| `grades_analysis.py` | **Grades extractor and CIF calculator** → Portuguese/international transcript parsing, DGES admission comparison |
| `cv_analysis.py` | **Multimodal PDF/DOCX parser** → structured CV JSON (skills/experience/education) |
| `cv_builder.py` | **2-tab CV toolkit** (quiz→ build CV, cover letters) → ReportLab PDF + JSON export |
| `university_finder.py` | **University degree search** (Portugal DGES + International Gemini search) → save favorites, grade comparison |
| `interview_simulator.py` | **Mock interviews** (Quick Practice 3-5Q + Mock 10Q) with STAR feedback scoring (1-10) |
| `student_resources.py` | **Student support tools** (exam papers, scholarships, study resources, wage finder) |
| `resources.py` | **Professional support tools** (job search, courses, LinkedIn optimizer, company research) + function calling chat |
| `student_chat.py` | **Student dashboard AI** (5Q rule → tool recs: "Career Quiz would suit you best") |
| `professional_chat.py` | **Professional dashboard AI** (5Q rule → "CV Analysis would suit you best") |
| `tools.py` | **Built-in tool definitions** (shared search tools for both student and professional resources) |
| `professional_tools.py` | **Function calling tool definitions** for professional support chat (get_career_roadmap, analyze_skill_gaps, etc.) |
| `models.py` | **Model configurations** (gemini-2.5-flash settings, temperature presets per feature: 0.1–0.9) |
| `prompts.py` | **Centralized prompt templates** (30+ prompts organized by module with .format() placeholders) |
| `schemas.py` | **Schemas and fallbacks** (CV extraction schema, fallback questions, dropdown options for UI) |
| `.env` | **API secrets** (Gemini/Langfuse keys) - **do not commit to Git!** (.gitignore protected) |
| `requirements.txt` | **Core dependencies** for pip install (streamlit, google-generativeai, langfuse, etc.) |

---

## Data Flow

### Example: Career Discovery Quiz

1. User Input: Student answers adaptive personality question
2. Service Layer: gemini_service sends prompt to Gemini with conversation history
3. AI Generation: Gemini generates next adaptive question based on previous answers
4. Observability: Langfuse logs trace
5. UI Update: Streamlit displays next question
6. Repeat: 10 questions total
7. Final Analysis: Gemini analyzes all answers, generates career sector matches
8. Storage: Report saved to SQLite via database.py, accesible in "My reports" section
9. Display: Results shown with sector percentages and recommended degrees

---

## AI Integration

### LLM Configuration

#### Temperature Guide

| Temperature | Use Case | Files |
|-------------|----------|-------|
| 0.1 | Extraction, parsing | CV extraction, grades extraction |
| 0.2 | Structured output | Degree questions |
| 0.3 | Analysis with facts | CV feedback, career quiz analysis |
| 0.4 | Conversational | Dashboard chats, polish CV |
| 0.5 | Search/recommendations | University search, interview questions |
| 0.6 | Reports | Interview feedback, career reports |
| 0.7 | Creative + function calling | Cover letters, resource chat |
| 0.9 | Adaptive/creative | Student career quiz questions |

---

### Feature-Level AI Configuration

Complete reference of model settings, temperature rationale, and prompt strategies per feature:

| Feature | Model | Temp | Prompt Strategy | Rationale |
|---------|-------|------|-----------------|-----------|
| **Student Career Quiz** | gemini-2.5-flash | 0.9 | Creative personality questions with adaptive follow-ups based on previous answers | High creativity needed for non-academic questions that reveal thinking patterns |
| **Career Growth Quiz** | gemini-2.5-flash | 0.3 | CV-aware behavioral questions across experience/skills dimensions | Analytical tone for professional assessment while maintaining conversational flow |
| **Degree Picker** | gemini-2.5-flash | 0.2 | Yes/no questions that narrow DGES degree options based on sector preference | Structured output needed for binary decision tree logic |
| **Grades Analysis (Extract)** | gemini-2.5-flash | 0.1 | Vision extraction of subject names and grades from uploaded images | Precision required for accurate data extraction from varied formats |
| **Grades Analysis (Calculate)** | gemini-2.5-flash | 0.1 | Apply Portuguese CIF formula: (school_avg × 0.65) + (exam_avg × 0.35) | Deterministic calculation with no creative freedom |
| **University Finder (Portuguese)** | N/A (DB Query) | N/A | SQL query against DGES dataset with location/grade filters | No AI generation - direct database lookup |
| **University Finder (International)** | gemini-2.5-flash | 0.5 | Search and summarize universities offering {degree} in {country} | Moderate creativity for recommendation synthesis |
| **Student Resources (Quick Search)** | gemini-2.5-flash | 0.7 | Built-In Tools: get_study_resources_web, get_wage_info, get_career_options | Creative search query formulation with factual grounding |

| **CV Analysis (Extract)** | gemini-2.5-flash | 0.1 | Vision extraction of skills, experience, education into JSON schema | Precision required for structured data extraction |
| **CV Analysis (Feedback)** | gemini-2.5-flash | 0.3 | Benchmarking analysis with actionable optimization tips | Analytical feedback grounded in job market standards |
| **Interview Simulator (Generate Qs)** | gemini-2.5-flash | 0.5 | CV-aware questions for {role} at {company}: behavioral, technical, situational | Balanced creativity for realistic interview scenarios |
| **Interview Simulator (Feedback)** | gemini-2.5-flash | 0.6 | STAR method evaluation with scoring (1-10) and improvement suggestions | Structured feedback with moderate creativity for constructive criticism |
| **CV Builder (Build from Quiz)** | gemini-2.5-flash | 0.4 | Transform quiz responses into professional CV JSON with polished bullet points | Conversational input to formal output transformation |
| **CV Builder (Tailor to Job)** | gemini-2.5-flash | 0.4 | Reorder CV bullets and inject keywords from job description | Moderate precision for ATS optimization |
| **CV Builder (Cover Letter)** | gemini-2.5-flash | 0.7 | Generate 200-350 word letter matching CV + job description in professional/enthusiastic tone | Higher creativity for personalized narratives |
| **Professional Resources (Quick Search)** | gemini-2.5-flash | 0.7 | Built-In Tools: get_job_search_results, get_course_recommendations, get_company_research | Creative search formulation with factual grounding |
| **Professional Resources (Support Chat)** | gemini-2.5-flash | 0.7 | Personalized career guidance using: calculate_career_readiness, compare_career_paths, analyze_skill_gaps, get_career_roadmap | Conversational advice with access to professional profile data with function calling |
| **Dashboard Chat (Student)** | gemini-2.5-flash | 0.4 | 5-question routing: ask about challenges → recommend tool with reasoning | Conversational tone for natural guidance flow |
| **Dashboard Chat (Professional)** | gemini-2.5-flash | 0.4 | 5-question routing: ask about frustrations → recommend tool with reasoning | Conversational tone for natural guidance flow |

---

### Prompt Template Organization

All prompts centralized in `config/prompts.py` grouped by module:

- **StudentCareerQuizPrompts** - 10Q adaptive personality assessment
- **CareerGrowthQuizPrompts** - 12Q CV-aware professional assessment
- **DegreePickerPrompts** - Binary decision tree for DGES degrees
- **GradesAnalysisPrompts** - Vision extraction + CIF calculation
- **CVAnalysisPrompts** - Vision extraction + feedback generation
- **InterviewSimulatorPrompts** - Question generation + STAR feedback
- **CVBuilderPrompts** - Build/tailor/cover letter generation
- **ResourceChatPrompts** - Function calling + personalized guidance
- **DashboardChatPrompts** - 5Q routing logic for both user types

Each prompt template uses `.format()` placeholders for dynamic insertion of user data (CV JSON, quiz results, saved universities, etc.).

---

#### Common Patterns

#### Standard LangfuseGeminiWrapper setup:
```python
from config import ModelConfig

CLIENT = LangfuseGeminiWrapper(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model=ModelConfig.MODULE_CONFIG["model"],
)
```

#### Standard prompt call:
```python
from config import ModulePrompts

prompt = ModulePrompts.PROMPT_NAME.format(
    param1=value1,
    param2=value2
)

response = CLIENT.generate_content(
    prompt=prompt,
    system_instruction=ModulePrompts.SYSTEM_INSTRUCTION,
    temperature=ModelConfig.MODULE_CONFIG["temp"],
    user_id=get_user_id(),
    session_id=get_session_id()
)
```

#### Standard fallback pattern:
```python
from config import FallbackQuestions

try:
    # AI generation
    questions = generate_questions_ai()
except Exception as e:
    st.error(f"Using fallback: {e}")
    questions = FallbackQuestions.FALLBACK_NAME
```


#### Prompt Engineering Strategy

Structured Outputs: Using markdown formatting for parseable reports
System Instructions: Persona definitions and clear prompts for consistent tone
Example: "You are a creative career counselor for Portuguese students. Ask unexpected questions that reveal thinking styles, not direct career preferences."

**Client Prompts**:
- accessible at config/prompts.py

---

---

## Multimodal Processing

### CV Analysis Feature

**Capability:** Upload PDF/DOCX/image → Gemini vision extracts structured JSON → Saves to database for cross-feature use

**Implementation:**
1. **Multimodal Input:** Gemini vision processes any format directly (no OCR libraries)
2. **Two-Phase Extraction:** 
   - Phase 1 (temp 0.1): Parse document into JSON (skills, experience, education)
   - Phase 2 (temp 0.3): Generate benchmarked feedback
3. **Storage:** Dual storage in `user_cvs` (active CV) and `professional_reports` (analysis history)
4. **Integration:** CV JSON feeds Career Growth Quiz, Interview Simulator, CV Builder

**Why:** No OCR dependency, handles messy formats, structured output enables cross-feature data flow

---

### Grades Analysis Feature

**Capability:** Upload grade report image OR manual input → Extract subjects/scores → Calculate CIF → Compare to saved universities

**Implementation:**
1. **Four Input Modes:** Portuguese (Upload/Manual), International (Upload/Manual)
2. **Vision Extraction (temp 0.1):** Parse grade report into JSON with subjects + scores
3. **CIF Calculation:** Apply Portuguese formula `(school_avg × 0.65) + (exam_avg × 0.35)`
4. **Integration:** CIF score filters University Finder search, compares to saved university thresholds

**Why:** Format agnostic, automatic calculation (no manual errors), feeds University Finder for realistic target matching

---

## Observability & Monitoring

### Langfuse Integration

Implementation: Custom wrapper (LangfuseGeminiWrapper) around Gemini API calls

What We Track:
- All LLM generations (prompts, outputs, token usage)
- User sessions and conversation flows
- Quiz question generation patterns
- Error rates and failure patterns

Why:
- Debug adaptive quiz logic (why certain questions generated)
- Monitor costs (token usage per feature)
- Improve prompts based on output quality
- Track user engagement patterns

---

## Deployment

### Platform: Streamlit Cloud

Why Streamlit Cloud:
- Free tier sufficient for our project
- Native Streamlit support
- Automatic deployment from GitHub
- Built-in secrets management

### Environment Variables

Required:
- GOOGLE_API_KEY: Gemini API access
- LANGFUSE_PUBLIC_KEY: Observability
- LANGFUSE_SECRET_KEY: Observability
- LANGFUSE_HOST: cloud.langfuse.com

Optional:
GOOGLE_CLIENT_ID; GOOGLE_CLIENT_SECRET: For google login

---

## Future Enhancements

### Potential Additions

1. RAG Implementation: If degree database grows beyond context limits (mentioned below)
2. Mobile Optimization: Responsive design for phone usage, different interface choice
3. Advanced Analytics: Career trend predictions, for example
4. More robust database implementation for scalability (mentioned below)


### Scalability Considerations

Our current architecture supports hundreds of concurrent users (Streamlit Cloud limits) and SQLite is sufficient for thousands of user records.
If scaling was needed we could migrate to PostgreSQL (relational data), add Redis for session caching and deploy to AWS/GCP for higher throughput
RAG implementation could support thousands of university programs via vector similarity matching beyond Gemini's context window. Advanced analytics could integrate salary trends and employment statistics.

---

End of Architecture Documentation
