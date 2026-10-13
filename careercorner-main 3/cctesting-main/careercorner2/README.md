# README
<img src="data/careercornermini.png" alt="Description" width="50%">

# Career Corner

Helping you build your career, every step of the way.


## Overview

Career Corner is an AI-powered application designed to help high-school students and professionals make informed career decisions. Whether you're a high-school student preparing for exams and struggling to pick a degree, or a professional seeking a career change or job opportunities based on your skills, Career Corner provides comprehensive support through two dedicated interfaces: one for high-school students and another for university students and professionals.
As former high-school students and aspiring data scientists themselves, the creators of Career Corner have experienced firsthand the lack of clear guidance during critical career processes: vague psychotechnical tests at school that fail to reveal true interests, scattered information making degree selection overwhelming, and lack of helpful information for professionals who are trying to identify transferable skills or navigating daily job struggles.

Career Corner aims to solve these challenges by combining conversational AI, real Portuguese educational data, and practical career tools to deliver personalized guidance far superior to traditional generic advice. Portuguese high school students benefit from adaptive career quizzes, CIF grade calculators, degree/university matchers with interactive maps, and study resources including IAVE exam archives and DGES degree data. Professionals access CV parsing, CV-aware career growth quizzes and tailored mock interview simulators with STAR feedback. 
Both user types can enjoy smart chat interfaces that route them to optimal tools and have the ability to save all results to "My Reports" for usage in other tools and persistent access across sessions, connecting school performance and career pathways in one cohesive platform.


**Target Audience:**
- **High school students** (Career and degree discovery, Grade calculation/preparing for university admission)
- **University students & professionals** (CV analysis, Career Recommendations, Interview preparation)
- **Focus (student section):** Portuguese education system (DGES degrees, National exams); Although tools are also available for international students.

---

## The Problem

### For Students:

Students face psychotechnical tests at school that don't connect interests to real university options, yielding vague results that don't help in decision making. Grades exist in isolation requiring manual calculation of the final highschool grade in order to find suitable degrees.

- Vague school career tests lacking personalization
- Confusion about degree choices and university options
- No real time connection between grades, interests, and real admission data
- Information scattered across multiple platforms (DGES, university sites)


### For Professionals:

Professionals send CVs everyday but get no structured skill analysis or interview practice catered to their needs, which might be beneficial if they want to succeed. Additionally, some professionals might want a career change but don't know what skills they can explore.

- Difficulty identifying transferable skills for career changes
- Generic job search tools without personalized insights
- No structured way to connect CV strengths to career paths
- Overwhelming job market navigation


## Our Solution

Career Corner delivers personalized guidance through conversational AI that adapts to user responses. 
Students can answer 10 creative questions to get sector matches (i.e. Healthcare 60%, Technology 40%), use the sector match results to explore suitable degrees, upload grade reports (or manually input grades) for final score calculation and get matched to real DGES degrees/universities based on school performance, quiz results and location. 
Professionals can upload their CVs (that get parsed into structured JSON) to get feedback, play CV-aware career quizzes, practice mock interviews tailored by job offer (with feedback) and generate tailored cover letters. 
All results persist in a SQLite database, being easily accessible through a "My Reports" tab and reusable throughout all of Career Corner's features.

1. **Conversational AI:** Interactive quizzes that adapt to user responses (not static multiple-choice)
2. **Real Data Integration:** Uses DGES university data, admission grades, and Portuguese scholarship info
3. **Personalization:** Connects quiz results -> grades -> degree recommendations -> university matches
4. **Actionable and Interactive Tools:** for example, CV analysis, grades analysis, university search, career path recommendations
5. **Observability:** Langfuse tracking of AI interactions for quality assurance during app testing


## Features
Shared for all users:
- **Data Persistence:** SQLite database stores quiz reports, grades, saved universities, CVs.
- **Google OAuth Login:** Secure login with Google accounts.
- **Local Login:** Secure login with accounts created directly on the platform and stored in the database.
- **Dashboard:** A dashboard with an AI career assistant chatbot that interacts with users that aren't sure about how to navigate the app, asking ~5 genuine questions about their situation and redirecting them to the most suitable starting tool after understanding their needs. The chatbot never mentions tool names during the first 5 turns, building context through casual dialogue like "What challenges are you facing with your studies?" or "What's frustrating about your job search?" On turn 6+, it confidently recommends a feature (i.e. "Career Quiz would suit you best because...") with clear reasoning. Both student and professional dashboards use separate chat histories with dedicated trace IDs in Langfuse for observability.
- **Reports Section** A section where all results from quizzes and analyses can be accessed and deleted by the user.
- **Custom CSS styling** Custom green and yellow UI with animations.


### For students:

#### **Career Discovery Quiz**
- Career Discovery Quiz - an interactive quiz operated through AI, to help students figure out their most valuable skills and biggest interests. The quiz asks the students creative/philosophical questions that aren't related to school or studies (i.e. "If you found a hidden path, would you explore it, observe, or do nothing?"), in order to understand the students real personality. At the end, a sector, or a mix of sectors (such as Technology, Health, Business) is attributed to the student based on their answers. Aditionally, a report is delivered, highlighting possible career paths based on the student's answers.

- **What it does:** Interactive conversational quiz (10 questions) to understand user's personality
- **Output:** 
  - Career sector match (Technology, Health, Business, Arts, etc.)
  - Top 3-5 degree recommendations with fit scores
  - Detailed report with reasoning
- **Tech:** Multi-turn chat with Gemini 2.5-flash, response validation

#### **Grades Analysis**
- Grades Analysis - A guided tool that collects school grades (through manual input or file ingestion) and calculates Portuguese final grades, helping students understand their academic profile, how far they are from getting into a certain university, and use this grade to find a university that they can get in.

- **What it does:** Calculates CIF using the official Portuguese formula or other formulas the student may want to use. The user can either manually input their grades or upload a grade report image for the AI to extract subjects and grades automatically, and enter their planned or completed exam scores to see their final score. Four options are available: Portuguese (Manual Input/Upload) and International (Manual Input/Upload).
- **Output:** 
  - Final score (e.g., 15.8/20)
  - Comparison to saved university thresholds from University Finder (Portuguese Students)
 
- **Tech:** Gemini multimodal vision for PDF/image parsing if upload option is selected

#### **Degree Picker**
An interactive assistant that uses the students sector of interest (results from career quiz if applicable) to suggest concrete degree programs, narrowing the search down to a shortlist of degrees that best fit the student. A portuguese (DGES only degrees) and international options are available.
- **What it does:** AI assistant that asks 5-7 yes or no questions based on the sector of interest and narrows down degree choices through conversation
- **Input:** Career quiz results (if available), student preference (manually picked from a dropdown list)
- **Output:**
- Portuguese Students:
  - Top 3 DGES degrees with:
    - Fit percentage
    - Curriculum overview
    - Career paths in Portugal
    - Entry requirements
- International Students:
  - Top 3 degrees with:
    - Fit percentage
    - Curriculum overview
    - Career paths
- **Tech:** RAG-style retrieval from DGES data, Gemini reasoning

#### **University Finder**
A university search tool by degree name and location. Two options are available:

- **Portuguese**: university search uses real Portuguese real DGES admission data from 2024-2025 to show universities offering the chosen degree (can be chosen from the results of **Degree Picker**), including entry grades, location and an interactive map so students can explore their options. Favorite universities can be saved to compare later or match against **Grades Analysis** score to see which are realistic targets.
- **International**: more "search" based interface, where students can input degree names and search for universities offering that degree in the country of their choice.

- **What it does:** Search and filter Portuguese universities by degree program using live DGES data
- **Features:**
  - **Location Filter:** Lisbon, Porto, Coimbra, or nationwide search
  - **Public/Private Toggle:** Filter tuition types
  - **Interactive Map:** Folium map with university markers, click to see admission grades and additional info
  - **Save System:** Store favorite universities with timestamps, access in My Reports
  - **Individual Delete:** Remove saved universities one-by-one
  - **Transferable result** Saved universities can be used in Grades Analysis
- **Output:** University cards showing institution name, program name, location, admission grade, duration
- **Tech:** DGES dataset (20+ universities), Folium map, SQLite saved_universities table with user_id tracking

#### **Student Resources**
Dual-mode feature combining five quick search options and support chat. Quick search mode provides instant access to study materials, scholarships, exam archives, career information, and wage data through 5 built-in Google Search tools. Support chat mode allows natural guidance conversations where you can select degree/grades reports from dropdowns and ask for more personal and catered advice (the AI can understand what the student needs and call a function accordingly).

- **Quick Search Features:**
  - **Study resources:** Google searches study resources for any subject
  - **Career paths:** Discover what careers you can pursue with your degree
  - **Wage finder:** Salary data by job title and country
  - **Scholarships:** DGES bolsas, FCT grants, Erasmus+ programs (Portuguese only)
  - **Past Exam papers:** IAVE nacional exam archives (all subjects, past years - Portuguese only)

- **Tech:**
  - Quick Search: Built-in Google Search tools (`get_study_resources_web`, `get_career_options`, `get_wage_info`, `get_scholarships`, `get_exam_papers`)


### For Professionals:

#### **CV Analysis**
Upload any PDF or DOCX CV and the AI extracts structured data: skills (technical like Python/SQL + soft like leadership), work experience (roles, companies, years, achievements), education background, and hidden strengths. Saved CVs auto-load on login via My Reports. The parsed JSON feeds directly into Career Growth Quiz for personalized questions and CV Builder for tailored cover letter generation. Get benchmarking against job market standards and actionable optimization tips like "Add metrics to your achievements" or "Highlight AWS experience more prominently."
- CV Analysis - A CV document parser that scans uploaded CVs (can be auto-reloaded from database on login), extracting skills, experience, achievements, and strengths into structured insights. It highlights what makes your profile stand out, benchmarks against job market standards, suggests optimizations and feeds directly into the Career Growth Quiz for hyper-personalizer recommendations, or into the CV editor to enhance it or cater it to a specific job offering and position.

- **What it does:** Multimodal CV parser using Gemini vision to handle any PDF/DOCX/image format
- **Extracts:**
  - Technical skills (programming languages, tools, certifications)
  - Soft skills (leadership, communication, problem-solving)
  - Work experience (job titles, companies, duration, bullet achievements)
  - Education (degrees, institutions, graduation years)
  - Strengths (what makes profile stand out)
  - Gaps (missing keywords or experience for target roles)
- **Features:**
  - Auto-reload: Saved CVs appear in My Reports CV selector dropdown
  - Benchmarking: Compares your profile to industry standards
  - Optimization tips: "Add quantified achievements" or "Strengthen technical section"
  - Integration: Parsed JSON flows to Career Quiz + CV Builder
- **Tech:** Gemini 2.5 Flash multimodal (handles scanned PDFs, images, any format), JSON storage in professional_reports table

#### **Career Growth Quiz**
An immersive 12-question conversational quiz designed for professionals and university students seeking career advancement or transitions. If you've uploaded a CV, questions adapt to your experience (e.g., "Given your 3 years in data analysis, how do you handle ambiguous stakeholder requests?"). Without a CV, questions focus on work preferences and soft skills. The quiz covers two phases: Experience & Preferences (6Q about teamwork, pressure, autonomy) and Soft Skills (6Q about leadership, communication, adaptability). Final report provides career sector match, growth paths (management track vs technical specialist vs entrepreneurship), skills to develop next, and 3-month action plan.
- Career growth quiz - an interactive, immersive quiz operated through a conversational AI interface, made for professionals find possible  figure out their most valuable skills and biggest interests. At the end, a sector (such as technology, health, business) is attributed to the student. Aditionally, a report is delivered, highlighting possible career paths based on the student's answers.

- **What it does:** CV-aware conversational assessment across experience preferences and soft skills dimensions
- **Input:** Parsed CV data (optional), work history, professional goals
- **Output:** 
  - Career sector match with reasoning
  - Growth path recommendations (management, technical deepening, lateral moves, entrepreneurship)
  - Top 3 skills to develop with concrete next steps
  - 3-month action plan with resources
  - Profile summary describing your work style
- **Tech:** Gemini 2.5 Flash, CV JSON integration, auto-saves to professional_reports

#### **CV Builder**
Two AI-powered tools in one interface. Build CV from scratch using a 5-step quiz (personal info -> education -> experience -> skills -> achievements) that generates a polished CV with your target job/industry. Generate cover letters by combining your CV data with a job posting into personalized 200-350 word letters. All outputs export as pretty PDFs using ReportLab (custom fonts, colors, professional layouts) plus JSON backups.

- **What it does:** Three modes in one tabbed interface
  1. **Build CV Quiz (Tab 1):** 5-step guided quiz collecting name/email, education, work experience, skills, achievements -> AI polishes into complete CV JSON
  2. **Cover Letter (Tab 2):** Uses CV data + job description -> generates 200-350 word letter in professional/enthusiastic tone
- **Output:** 
  - Pretty PDF CVs with custom ReportLab styling (DM Sans font, lime/yellow branding)
  - JSON backup downloads for editing
  - TXT cover letters ready to paste
- **Tech:** Gemini 2.5 Flash, ReportLab PDF generation, auto-saves to professional_reports

#### **Interview Simulator**
Practice job interviews with AI-generated questions tailored to your CV and target role. Quick Practice mode (10-15 mins) lets you select focus areas (Behavioral, Technical, Situational) for 3-6 questions with instant per-answer feedback. Mock Interview mode (30 mins) generates 10 role-specific questions for full interview simulation with comprehensive feedback report including overall score (1-10), best answer, answer that needs work, STAR method analysis, and recommended practice areas. Upload cover letter for even more personalized questions.

- **What it does:** Two modes for interview practice with AI feedback
  - **Quick Practice:** Select focus areas (Behavioral/Technical/Situational/Strengths-Weaknesses/Career Goals) -> 3-6 questions -> instant feedback per answer
  - **Mock Interview:** Enter target role + company -> 10 comprehensive questions -> full feedback report
- **Features:**
  - CV-aware questions (references your experience if CV uploaded)
  - Cover letter upload for additional personalization
  - Progress tracking (Question 3 of 10)
  - Back/Next/Skip navigation
  - Text area for typed answers (1-3 minute responses)
- **Output:** 
  - Per-answer feedback (Quick Practice)
  - Comprehensive report (Mock Interview): overall score 1-10, strengths, areas for improvement, best answer analysis, answer that needs work with fixes, key takeaways, recommended practice
  - STAR method evaluation (Situation, Task, Action, Result)
- **Tech:** Gemini 2.5 Flash, CV JSON integration, session state for multi-question flow

#### **Professional Resources – Your Next Steps**
Dual-mode feature combining quick job/course search and support chat. Quick search mode surfaces real job postings (Portugal-focused) and online courses to grow your skills, while support chat lets you select CV/quiz reports from dropdowns so the AI can reference your actual profile when giving advice like "What roles fit my CV?" or "What courses close my skill gaps?".

- **Quick Search Features:**
  - **Job search:** Finds recent LinkedIn-style job postings matching your role, skills, and preferred location (Portugal-focused but can search globally)
  - **Course recommendations:** Suggests Coursera/Udemy-style courses of the user's choice
  - **Wage finder:** Salary data by job title and country
  - **LinkedIn/profile optimization:** Tips on headlines, About section, skills to highlight
  - **Company research:** Culture, benefits, reviews, salary ranges to assess potential employers
- **Support Chat Mode:**
  - Select saved CV and career quiz reports from dropdowns for personalization
  - AI reads your parsed skills, experience, and sector matches before answering
  - Ask: "Should I become a Data Scientist or Product Manager?", "Am I ready to be a Software Engineer?", "I want to become a [job role] - what skills am I missing?", "Show me a roadmap to become a [job role] in [timeframe]"
- **Tech:**
  - Quick Search: Built-in web tools (`get_job_search_results`, `get_course_recommendations`, `get_linkedin_profile_optimization`, `get_company_research`)
  - Support Chat: Gemini 2.5 Flash with function calling (`analyze_skill_gaps`, `get_career_roadmap`, `compare_career_paths`,
    `calculate_career_readiness`)


## Tech Stack

### Backend
- **Python 3.13** powers all files with clean separation (pages/services/utils)
- **Google Gemini API**
  - `gemini-2.5-flash`
- **SQLite** lightweight tempdir database (`/tmp/career_corner.db`) with 4 tables:
  - `professional_reports` (CV/quiz/grades results with cv_json)
  - `saved_universities` (user favorites with admission data)
  - `user_cvs` (parsed CV JSON with timestamps)
  - `users` (authentication with hashed passwords)
- **Langfuse v3.11.1** traces every Gemini call through `LangfuseGeminiWrapper`

### Frontend
- **Streamlit 1.40+** native Python web framework handles all UI:
  - Session_state for 10Q quizzes, mock interviews, multi-step workflows
  - Progress bars, tabs, expanders, chat interfaces, file uploaders
  - Back/Next navigation with `st.rerun()` for smooth UX
- **ReportLab 4.2.2** generates professional PDF CVs with custom DM Sans typography and lime/yellow branding

### Database
- **SQLite tempdir** (`/tmp/career_corner.db`) provides zero-config persistence:
  - **Why perfect:** No external hosting, survives Streamlit restarts, automatic `init_database()` creates all tables
  - **Handy for production:** Works instantly on Streamlit Cloud, no connection strings/secrets needed
  - **Scales to 1000s:** Handles thousands of user reports/universities with indexes on user_id/report_type
  - **Structured data:** CV JSON, university data, timestamps enable My Reports dropdowns

### Authentication
- **Werkzeug 3.0.4** secure password hashing (`generate_password_hash/check_password_hash`)
- **Google OAuth 2.0** via native client credentials with localhost/production redirect URIs
- **Session management** through `st.session_state.logged_in` + `st.session_state.username`

### AI & Tools
- **Langfuse** production observability wrapping most of Gemini calls (tools and function calling aren't wrapped but are still monitored using @observe):
  - Traces prompts, responses, tokens, temperature, and metadata per generation  
  - User feedback scoring (thumbs up/down → 0.0–1.0)
  - Conversation turn tracking (multi-turn chat routing validation)
  - Feedback mechanisms hidden in deployment version

- **Two AI tool architectures** (17 tools total)
  - **1. Built-in tools** (Google Search & URL Context) – 7 tools  
     - Study resources finder (courses, videos, tutorials)  
     - Career options explorer (job paths, progression, salaries)  
     - Wage information lookup (by country and role)  
     - Job search aggregator (LinkedIn, Indeed, Glassdoor, company sites)  
     - Course recommendations (Coursera, Udemy, edX, etc.)  
     - LinkedIn profile optimizer (headline, About, skills, strategy)  
     - Company research tool (culture, reviews, news, salaries)  

  - **2. Function calling tools** (custom Python functions) –  4 tools
    
     **Professional tools (4 functions)**  
     - `analyze_skill_gaps` – Compare current CV skills vs target role requirements, compute gaps and recommendations  
     - `get_career_roadmap` – Generate phased career roadmap (e.g., 6 months / 1 year / 2 years) based on stored data
     - `compare_career_paths`- Compare two careers based on suitability for user
     - `calculate_career_readiness` - Tell user how ready they are (on a scale of 0-100%) for a certain career

   All function calling tools use:
   - 3-attempt retry logic for robustness  
   - Structured JSON responses  
   - Central dispatchers and observability for monitoring  

    - **Usage Pattern:**
      - **Quick Search/Quick Tools pages:** Use built-in tools (7 tools total) for real-time web searches
      - **Career Support Chat:** Use function calling tools (4 tools total) to access user's saved database records and get personalized answers

- **Multimodal AI** (Gemini vision)
  - CV parsing: PDF/DOCX → structured JSON (skills, work experience, education)  
  - Grade reports: images → extracted subject scores → used in CIF/admission calculations  


### Data Sources
- **IAVE** national exam archives (past papers, all subjects/years)
- **Scholarships** DGES/FCT/Erasmus+ direct program links
- **Google** data available publicly online
- **No external APIs** - all resources retrieved via URLs + built-in google tools + function calling


## Architecture

Career Corner follows a modular layered architecture for maintainability and scalability:

- **Presentation Layer** (`pages/`) - 14 Streamlit UI files, one per feature, with independent session state management
- **Service Layer** (`services/`) - Authentication (both local and google logins), Langfuse wrapper (LangfuseGeminiWrapper), and tool definitions (built-in + function calling tools)
- **Data Layer** (`utils/`) - SQLite database operations and report rendering
- **Configuration Layer** (`config/`) - Centralized AI settings, prompts, and schemas in three separate files
- **Styling Layer** (`styles.py`) - Custom CSS with DM Sans fonts and lime/yellow theme


### Project Structure
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
│ ├── logo2.png
│ ├── mini.png
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


**Key architectural decisions:** Dual dashboard design (student/professional), database-first persistence (SQLite tempdir), LangfuseGeminiWrapper pattern for observability, and one-file-per-feature modularity. For detailed architecture rationale, component breakdown, and design patterns, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## **Key Features to Highlight**

#### **Persistent Data Storage**
All quiz results, CVs, grades, and saved universities are stored in SQLite and automatically reload on login. Users can:
- Access past reports from any feature through "My Reports" tab
- Use saved data across features (e.g., CV in Interview Simulator, grades in University Finder)
- Delete individual items while preserving others
- Export reports as PDFs or JSON

#### **Auto-saving results**
- Avoids data loss

#### **Interactive Map (University Finder for Portuguese Students)**
- Click university markers on Folium map
- See admission grades, location, website
- Filter by CIF range

#### **Document Upload**
- Supports PDF and images (JPG, PNG)
- Multimodal Gemini extracts text from any format
- Works with messy/scanned documents

#### **Dropdown Selection in Resources Chat**
- Professional career support chat mode has dropdowns
- Select which CV report and Quiz results to reference (e.g., "CV: My Resume - 2025-12-11")
- AI uses selected report content for personalized answers


## Installation & Setup

### Prerequisites
### **Prerequisites**

- **Required Packages:**
  streamlit>=1.40.0
  google-generativeai>=0.8.3
  langfuse>=3.11.1
  python-dotenv>=1.0.1
  reportlab>=4.2.2
  werkzeug>=3.0.4
  sqlite3

- **Python 3.10+**
- **Google Gemini API Key:** [Get it here](https://ai.google.dev)
- **Langfuse Account (Optional):** [Sign up](https://langfuse.com)
- **Google OAuth Credentials (Optional)**


### How to set up GoogleOAuth login (optional):
#### ** Create Credentials (both local and deployment)**
  1. Go to [Google Cloud Console](https://console.cloud.google.com)
  2. Create new project → **"Career Corner"**
  3. Enable **Google+ API**
  4. **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
     - App type: **Web application**
     - Name: **Career Corner Streamlit**
  
  **2. Add Redirect URIs**
    ```
      https://your-app.streamlit.app (i.e. https://careercorner.streamlit.app)
      http://localhost:8501
    ```


### Local Installation Instructions

**Required environment variables (.env file):**
```bash
GOOGLE_API_KEY="your_gemini_api_key"
LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
LANGFUSE_HOST="https://cloud.langfuse.com"
```

**Optional environment variables:**
Keep your .env file simple (no REDIRECT_URI needed for local):
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

**Security Note:** 
- **NEVER commit `.env` to Git!** It's already in `.gitignore`
- For deployment, use Streamlit Secrets (see [Deployment](#deployment))


#### Steps
1. Clone the repository:
```bash
git clone https://github.com/antonia43/careercorner
cd careercorner
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (use your keys):
```bash
cp .env.example .env

```

4. Run the application:
```bash
streamlit run zapp.py  
```

**App will open at:** `http://localhost:8501`

**Note:** imports with structure `from utils.database import load_report` may yield errors. If thats the case, you can use directly `from database import load_report`.


---

## Deployment

**Deployment Platform:** Streamlit Cloud

### **Streamlit Cloud**
1. **Push Code to GitHub:**
```
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Deploy on Streamlit Cloud:**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click "New app"
- Select your GitHub repo (career-corner)
- Set main file: `zapp.py`

3. **Add Secrets:**
- In Streamlit Cloud dashboard -> "Settings" -> "Secrets"
- **Required Variables**:
```bash
GOOGLE_API_KEY="your_gemini_api_key"
LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
LANGFUSE_HOST="https://cloud.langfuse.com"
```

- **Additional Variables** (For Google Login):
```bash
GOOGLE_CLIENT_ID = "your_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "https://careercorner.streamlit.app"
```
  
4. **Deploy:**
- Click "Deploy"
- App will be live at your preferred https address

Note: ensure imports are using the right structure (e.g. from utils.database import load_report; not from database import load_report)


---

## Usage Guide

### First-Time Setup
1. **Launch App:** Run `streamlit run zapp.py` (opens http://localhost:8501) and `streamlit run authentication.py`(if using Google oAuth)
2. **Choose Dashboard:** 
   - **Student Dashboard** -> high school students planning university
   - **Professional Dashboard** -> university students/professionals job hunting
3. **Onboarding:** Confirm your user type
4. **Start Chat:** AI asks natural questions before recommending tools
5. **Usage:** Have fun! The app is very intuitive, it tells you all you need to know to properly navigate it.

---
**Example Workflow (Student):**

```
1. Dashboard Chat (2 mins)
├─ AI: "What challenges are you facing with your studies?"
├─ You: "I'm confused about what degree to pick"
└─ AI: "Career Quiz would suit you best because you're exploring options"
```

```
2. Career Discovery Quiz (10 mins)
├─ Answer 10 adaptive questions ("Perfect day starts with what sound?")
├─ Results: "Healthcare 60%, Education 40%"
└─ Auto-saves to My Reports
```

```
3. Degree Picker (5 mins)
├─ Select sector from quiz (Healthcare -> Nursing/Physiotherapy)
├─ Top 3 DGES degrees with entry requirements/CIF needed
└─ Auto-saves recommendations
```

```
4. Grades Analysis (10 mins)
├─ Enter your portuguese grades manually
├─ CIF calculation: School 65% + Exams 35% = 15.8/20
└─ Search for Course grades and compare them to yours, get your chances of getting in

```

```
5. University Finder (10 mins)
├─ Search "Nursing" universities matching your CIF 15.8
├─ Filter: Lisbon, public unis, 14.0-16.0 admission range
├─ Interactive map -> click Nova marker -> "CIF required: 15.2"
└─ Save favorite universities (accessible at the top of the page)
```

```
6. Student Resources (10 mins)
├─ Quick Search: "Biology study resources" → Khan Academy links, YouTube tutorials
├─ Wage Finder: "Nurse salary Portugal" → €1,200-€2,500/month
├─ Past Exams: Download IAVE Biology papers 2020-2024
├─ Switch to Support Chat → Select "Career Quiz: Healthcare 60%" from dropdown
└─ Ask: "Help me understand my results" → AI explains CIF competitiveness + career fit
```

**Example Workflow (Professional):**
```
1. Dashboard Chat (2 mins)
├─ AI: "What's frustrating about your job search?"
├─ You: "My CV isn't getting responses"
└─ AI: "CV Analysis would suit you best"
```

```
2. CV Analysis (5 mins)
├─ Upload CV (PDF/image)
├─ AI extracts skills, experience, strengths
├─ Get benchmarking + optimization tips
└─ JSON saved to My Reports
```
```
3. Career Growth Quiz (10 mins)
├─ CV-aware questions: "Given your data analysis exp, prefer teams or solo?
├─ 2 phases: Experience prefs (6Q) + Soft skills (6Q)
└─ Results: Receive personalized report (auto saved)
```

```
4. Interview Prep (30 mins)
├─ Mock Interview: "Senior Data Analyst @ Nova"
├─ 10 questions -> type answers (Situation/Task/Action/Result)
└─ Feedback: "Score 7.5/10, Best answer: Q3 leadership, Improve: Q7 metrics"
```
```
5. CV Builder (10 mins)
├─ Tab 1: Build new CV from quiz (5-step: info/education/exp/skills)
├─ Tab 2: Cover letter (350 words, enthusiastic tone)
└─ Download PDF CV + JSON backup and Branded ReportLab styling
```
```
6. Professional Resources (10 mins)
├─ Quick Search: Find "Python Developer" jobs in Lisbon
├─ Get Coursera/Udemy courses for missing skills
└─ Chat Mode: "What jobs match my CV?" with CV dropdown selected
```



## License

MIT License

Copyright (c) 2026 Antónia Lemos (antonia43 on github) and Matilde Maximiano

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## Team

- **Antónia Lemos** - Core development (student + professional features)
- **Matilde Maximiano** - Core development (student + professional features)


**Members contributed equally across:**
- Architecture design and implementation
- Feature development (student + professional dashboards)
- AI integration (Gemini API, Langfuse observability, prompt engineering)
- Database design and persistence layer
- Authentication system
- Deployment and documentation

**Institution:** Nova IMS, Universidade Nova de Lisboa  
**Course:** BSc in Data Science  
**Project:** AI Capstone Project  
**Completion:** February 2026

**GitHub:** https://github.com/antonia43/careercorner   
**Live Application:** https://careercorner.streamlit.app

**Career Corner** by Matilde Maximiano and Antónia Lemos (Nova IMS, February 2026)

---
