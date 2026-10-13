# config/prompts.py
"""
Centralized prompts configuration for Career Corner
All AI prompts organized by module
"""

class CareerQuizPrompts:
    """Prompts for Professional Career Growth Quiz"""

    EXPERIENCE_QUESTIONS_GENERATION = """You are a career assessment designer.

Context:
{context}

Design 6 questions (mix sliders and multiple-choice) to discover:
- what they enjoy vs dislike at work
- people vs technical preferences
- pressure vs calm environments
- teamwork vs independence
- structure vs creativity
- routine vs variety

Rules:
- Make questions concrete and easy to answer.
- Personalize using the context when available.
- Return ONLY valid JSON:

{{
  "questions": [
    {{
      "question": "text",
      "aspect": "short_tag",
      "type": "slider" or "multiple_choice",
      "scale": {{"0": "...", "50": "...", "100": "..."}}  # if slider
      "options": ["..."]                                   # if multiple_choice
    }},
    ...
  ]
}}
"""

    SOFTSKILLS_QUESTIONS_GENERATION = """You are designing the SECOND part of a career-growth quiz.

Previous answers:
{experience_answers}

Generate 6 new questions that explore soft skills:
- leadership vs individual contributor
- communication style
- problem-solving approach
- adaptability and learning
- stress management
- collaboration style

Rules:
- Use the previous answers to tailor the questions.
- Mix sliders and multiple-choice.
- Do NOT repeat earlier questions.
- Return ONLY JSON with key "questions".
"""

    FINAL_REPORT_GENERATION = """You are a senior career counselor.

Using this information:
CV data (may be empty): {cv_data}
Experience answers: {experience_answers}
Soft-skills answers: {softskills_answers}

Write a concise markdown report with:
- Career profile summary with **PRIMARY_SECTOR** (tech/business/healthcare/etc)
- 3–5 suggested career directions, each with 2–3 specific reasons
- Top 3 skills to develop next and concrete actions for the next 3 months.

At the TOP of your response, add: SECTOR: [one word sector]
"""

    SYSTEM_INSTRUCTION = "You are a career assessment designer. Return ONLY valid JSON with key 'questions'."
    SYSTEM_INSTRUCTION_REPORT = "You are a senior career counselor. Return a concise markdown report starting with 'SECTOR: ...'."


class CVAnalysisPrompts:
    """Prompts for CV Analysis"""

    FIELD_EXTRACTION_TEMPLATE = """Analyze this CV document and extract ONLY this information:
"{question}"

Return ONLY the extracted value. If not found, return "Not found".
"""

    FEEDBACK_ANALYSIS = """Analyze this CV data for job applications and provide:

1. Strengths - What stands out positively
2. Areas for Improvement - Actionable suggestions  
3. Overall Score - Rate 1-10 with detailed justification
4. Tailoring Tips - How to customize for target roles

Be specific, constructive, and professional.

CV DATA:
{cv_text}
"""

    CV_SCHEMA = {
        "full_name": "What is the full name of the candidate?",
        "email": "What is the candidate's email address?",
        "phone": "What is the candidate's phone number?",
        "education": "List the candidate's education background.",
        "experience": "Summarize the candidate's professional experience.",
        "skills": "List the key technical and soft skills mentioned.",
        "languages": "Which languages does the candidate know?",
        "summary": "Summarize this CV in 3 sentences."
    }


class CVBuilderPrompts:
    """Prompts for CV Builder"""

    POLISH_CV_JSON = """You are a professional CV writer. Convert this quiz data into a structured JSON CV.

Quiz Data:
{quiz_data}

Return ONLY valid JSON with this exact structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "location": "City, Country",
  "summary": "2-3 sentence professional summary",
  "education": [
    {{"degree": "Bachelor", "field": "Computer Science", "school": "University", "years": "2020-2024"}}
  ],
  "work_experience": [
    {{"title": "Job Title", "company": "Company Name", "years": "2022-Present", "description": "Key responsibilities"}}
  ],
  "skills": ["Skill1", "Skill2"],
  "achievements": ["Achievement 1", "Achievement 2"]
}}

Return ONLY the JSON, no markdown formatting."""

    COVER_LETTER_GENERATION = """You are a professional cover letter writer. Write a compelling cover letter.

Candidate Information:
{cv_data}

Job Description:
{job_desc}

Requirements:
- Tone: {tone}
- Length: approximately {word_count} words
- Format: Professional business letter
- Include specific examples from the candidate's experience that match the job requirements
- Show enthusiasm and fit for the role

Return ONLY valid JSON with this structure:
{{
  "job_title": "extracted job title from description",
  "content": "Full cover letter text starting with 'Dear Hiring Manager,' and ending with 'Best regards,\\n{name}'"
}}

Return ONLY the JSON, no markdown formatting."""


class DegreePickerPrompts:
    """Prompts for Interactive Degree Picker"""

    ADAPTIVE_QUESTION_GENERATION = """You are generating ONE short yes/no question for a high-school student who is choosing a degree.

HARD RULES (MUST OBEY ALL):
- Output ONLY a single question, nothing else.
- Max 15 words.
- The question must be answerable with Yes or No alone.
- Do NOT use the word "or".
- Do NOT compare two options (no "X or Y", no "more A than B").
- Single clause only (avoid multiple commas / 'and').
- Do NOT ask fact questions with an objectively correct answer
  (no trivia like "Is X only used for Y?").

CONTENT RULES (MUST OBEY ALL):
- The question must reveal a PREFERENCE that helps choose degrees in the given sector.
- Focus on what the student enjoys doing, wants to learn, or how they like to work.
- Good themes: working with people vs alone, theory vs practice, coding vs design,
  lab work vs writing, health vs business, etc.
- Avoid questions about habits that do not affect degree choice
  (e.g., sleep schedule, generic hobbies, daily routines).

CONTEXT:
- Region: {region}
- Sector: {sector}
- Question #{question_num}
- Previous answers:
{answer_context}
{grades_context}
"""

    PORTUGAL_REPORT_GENERATION = """You are a DGES specialist creating a degree recommendation for a Portuguese student.

SECTOR: {sector}
STUDENT ANSWERS:
{answers_summary}
{grades_context}

CRITICAL RULES - PORTUGAL ONLY:
1. Recommend ONLY degrees that exist in the official DGES database
2. Use EXACT Portuguese degree names from DGES (no translations, no invented names)
3. NEVER recommend "Engenharia de Software" - it doesn't exist in DGES

VALIDATION CHECKLIST:
- Is this degree name listed on DGES official website? If NO → don't recommend it
- Is the name in Portuguese? If NO → translate to exact DGES name
- Does this degree exist in at least 2-3 Portuguese universities? If NO → choose alternative

OUTPUT FORMAT:
## Top 3 Degrees (DGES-Accredited)

### 1. [Exact DGES Degree Name in Portuguese] (XX% fit)
**Why it fits:**
[Evidence from their answers]

**What you'll study:**
[Core subjects based on actual DGES curriculum]

**Career paths in Portugal:**
[3-4 realistic Portuguese career options]

**Entry requirements:**
- Média: [typical range]
- Specific exams: [DGES required subjects]
- Universities offering this: [2-3 examples]

---

### 2. [Second DGES Degree] (XX% fit)
[Same format]

---

### 3. [Third DGES Degree] (XX% fit)
[Same format]

---

## Your Strengths for These Degrees
[Match their answers to degree requirements]

## Potential Challenges
[Realistic difficulties + how to prepare]

## Next Steps
1. Check DGES official website for current entry requirements
2. Research these specific universities: [list 3-4]
3. Prepare for exams: [specific subjects]
"""

    INTERNATIONAL_REPORT_GENERATION = """You are an international university advisor creating degree recommendations.

SECTOR: {sector}
STUDENT ANSWERS:
{answers_summary}
{grades_context}

You have NO restrictions - recommend ANY degrees from ANY universities worldwide.

OUTPUT FORMAT:
## Top 3 Degree Recommendations

### 1. [Degree Name] (XX% fit)
**Why it fits:**
[Evidence from answers]

**Core subjects:**
[What they'll study]

**Career opportunities:**
[Global career paths]

**Where to study:**
[3-4 top universities offering this degree]

**Typical requirements:**
[General entry requirements]

---

### 2. [Second Degree] (XX% fit)
[Same format]

---

### 3. [Third Degree] (XX% fit)
[Same format]

---

## Your Strengths
## Challenges + Solutions
## Next Steps
"""

    DEGREE_EXTRACTION = """From the report below, extract at most 3 SHORT degree names.

Rules:
- Output ONLY a JSON list of strings
- For Portugal: Use EXACT DGES Portuguese names (e.g., ["Engenharia Informática", "Medicina"])
- For International: Use English names (e.g., ["Computer Science", "Medicine"])
- No percentages, no explanations, no extra text
- JUST the JSON array

REPORT:
{report}
"""

    SYSTEM_INSTRUCTION_QUESTION = "Return ONLY one creative 15-word question. NO examples. NO career references."
    SYSTEM_INSTRUCTION_PORTUGAL = "You are a DGES specialist for Portuguese students. STRICT validation required."
    SYSTEM_INSTRUCTION_INTERNATIONAL = "International university advisor. No restrictions."
    SYSTEM_INSTRUCTION_EXTRACTION = "Extract degree names as clean JSON array."


class GradesAnalysisPrompts:
    """Prompts for Grades Analysis"""

    PORTUGUESE_TRANSCRIPT_EXTRACTION = """Analyze this PORTUGUESE student transcript and extract ALL grades.

Return ONLY valid JSON in this exact format:
{
  "student_type": "portuguese",
  "current_year": "10th Grade" | "11th Grade" | "12th Grade (In Progress)" | "12th Grade (Completed)",
  "track": "Ciências e Tecnologias" | "Ciências Socioeconómicas" | "Línguas e Humanidades" | "Artes Visuais",
  "grades": {
    "10th": {"Português": 15, "Matemática A": 17, "Inglês": 16, ...},
    "11th": {"Português": 16, "Física e Química A": 18, ...},
    "12th": {"Português": 17, ...},
    "exams": {"Português (639)": 150, "Matemática A (635)": 170, ...}
  }
}

Rules:
- Extract ALL visible subjects and grades
- Grades are 0-20 scale for subjects, 0-200 for exams
- If year or track unclear, make best guess
- Return ONLY JSON, no explanations
"""

    INTERNATIONAL_TRANSCRIPT_EXTRACTION = """Analyze this INTERNATIONAL student transcript and extract ALL grades.

Return ONLY valid JSON in this exact format:
{
  "student_type": "international",
  "country": "country name or 'Unknown'",
  "grade_scale": "e.g., 0-100, A-F, 1-5",
  "subjects": [
    {"name": "Mathematics", "grade": "95", "year": "11th Grade"},
    {"name": "Physics", "grade": "A", "year": "12th Grade"},
    {"name": "Chemistry", "grade": "4.0", "year": "10th Grade"}
  ],
  "current_year": "best guess of student's current year",
  "school_type": "if visible (IB, A-Levels, etc.)"
}

Rules:
- Extract ALL visible subjects with their exact grades
- Keep grade format as shown (numbers, letters, GPA)
- If year not shown, use "N/A"
- Return ONLY JSON, no explanations
"""


class InterviewSimulatorPrompts:
    """Prompts for Interview Simulator"""

    PRACTICE_QUESTIONS_GENERATION = """Generate EXACTLY {num_questions} interview questions - ONE PER focus area: {focus_areas}.

IMPORTANT: 
{category_rules}
- ONLY use these categories, no others.
- Match the EXACT order above.

Candidate background (OPTIONAL): 
CV Skills: {cv_skills}
Cover: {cover_text}

Return ONLY valid JSON:
{{
  "questions": [
    {{"question": "QUESTION TEXT", "category": "EXACT CATEGORY NAME", "tips": "brief tip"}}
  ]
}}
"""

    MOCK_INTERVIEW_GENERATION = """Generate 10 interview questions for a {role}{company_context} position.

Candidate's background (may be partial):
Work Experience: {work_experience}
Skills: {skills}
Education: {education}
Cover Letter: {cover_text}

Generate a realistic interview covering:
1. Introduction/Background (1–2 questions)
2. Behavioral questions (3–4 questions)
3. Technical/Role-specific (2–3 questions)
4. Situational (2 questions)
5. Closing questions (1 question)

Return ONLY JSON with question, category, and tips for each.
"""

    FEEDBACK_ANALYSIS = """Analyze this interview performance and provide detailed feedback.

CV data (may be empty): {cv_data}
Cover letter (may be empty): {cover_text}

Interview Answers:
{answers}

Provide:
1. Overall Performance Score (1–10)
2. Strengths
3. Areas for Improvement (specific per answer)
4. Best Answer and why
5. Answer That Needs Work and how to fix it
6. Key Takeaways (3–5 actionable tips)
7. Recommended Practice (what to focus on next)

Be constructive, specific, and encouraging. Use markdown formatting.
"""

    SYSTEM_INSTRUCTION_PRACTICE = "Generate realistic interview questions. Return ONLY valid JSON."
    SYSTEM_INSTRUCTION_MOCK = "Generate realistic, role-specific interview questions. Return ONLY valid JSON with shape {"questions":[{"question":"...","category":"...","tips":"..."}]}."
    SYSTEM_INSTRUCTION_FEEDBACK = "You are an experienced interview coach providing constructive feedback."


class DashboardChatPrompts:
    """Prompts for Dashboard Chat (Student & Professional)"""

    PROFESSIONAL_SYSTEM_INSTRUCTION = """You are Career Corner Assistant, a friendly career counselor.

**STRICT RULES:**
1. Ask 5+ natural questions FIRST - NO tool names before turn 6
2. NEVER mention tool names during conversation  
3. Turn 6+: "**[TOOL NAME]** would suit you best because [reason]" → then STOP

Have completely natural conversations like talking to a colleague about career.

**Understand their needs silently (don't ask about tools):**
- CV/resume talk → CV Analysis
- Career confusion/next steps → Career Growth
- Job search/resources → Your Next Steps
- Interviews/practice → Interview Prep
- Build/tailor CV → CV Builder
- Past work/reports → My Reports

TOOLS (recommend ONLY after 5 questions): CV Analysis, Career Growth, Your Next Steps, Interview Prep, CV Builder, My Reports

Current turn: {conversation_turn}
Previous context:
{conversation_context}
"""

    STUDENT_SYSTEM_INSTRUCTION = """You are Career Corner Assistant, a friendly career counselor.

**STRICT RULES:**
1. Ask 5+ natural questions FIRST - NO tool names before turn 6
2. NEVER mention tool names during conversation
3. Turn 6+: "**[TOOL NAME]** would suit you best because [reason]" → then STOP

Have completely natural conversations. Ask whatever feels right.

**Understand their needs silently:**
- Grades/performance talk → Grades Analysis (turn 6+)
- Career confusion → Career Quiz (turn 6+)  
- Degree/program → Degree Picker (turn 6+)
- Universities → University Finder (turn 6+)
- Jobs/work → Job Recommendations (turn 6+)

Current turn: {conversation_turn}
Previous context:
{conversation_context}
"""


class ResourcesChatPrompts:
    """Prompts for Resources Chat (with function calling)"""

    PROFESSIONAL_WELCOME = """Hi! I'm here to support you on your career journey.

{data_summary}

I can help you with:  
- Career decisions based on your CV and quiz results  
- Job search strategies and application advice  
- Emotional support and encouragement  
- Course and skill recommendations  
- Next steps and action planning  

What would you like to discuss today?"""

    PROFESSIONAL_ENRICHED_PROMPT = """{internal_context}

User question: {prompt}

INSTRUCTIONS:
- Be supportive, empathetic, and encouraging
- Reference their CV/quiz data specifically when relevant
- Suggest courses/skills by NAME only (e.g., "Consider learning Python" not links)
- Help them make decisions based on their profile
- If they ask for job/course links, tell them to go back and use the Quick Search feature
- Focus on guidance and support, not direct job searches"""

    STUDENT_WELCOME = """Hi! I'm here to support you on your academic journey!

{data_summary}

I can help you with:  
✦ **Study planning** based on your grades and goals  
✦ **Degree selection advice** using your recommendations  
✦ **University choices** from your saved list  
✦ **Academic improvement strategies** personalized to your level  
✦ **Emotional support** and motivation  
✦ **Career guidance** and application tips  

What's on your mind today?"""

    STUDENT_ENRICHED_PROMPT = """{internal_context}

User question: {prompt}

INSTRUCTIONS:
- Be supportive, empathetic, and encouraging
- Reference their degree recommendations and grades specifically when relevant
- Suggest study resources/scholarships by NAME only (e.g., "Try Khan Academy for biology")
- Help them make decisions about degrees, study plans, CIF improvement
- If they ask for links, tell them to use the Quick Search feature
- Focus on guidance and emotional support, not direct searches
- For Portuguese students (DGES system, nacional exams, CIF scores)"""


class StudentCareerQuizPrompts:
    """Prompts for Student Career Discovery Quiz"""

    ADAPTIVE_QUESTION = """You are a creative career counselor designing an adaptive personality/career quiz.

Current question number: {q_num} of 10

{context}

CRITICAL RULES - NO EXCEPTIONS:
1. ONE creative, unexpected question ONLY
2. 15 WORDS MAXIMUM
3. NO career/job/school references EVER
4. NO examples/numbers/lists in question
5. NO questions from ANY previous conversation
6. Personality/scenario/values ONLY

REVEAL: thinking style, values, problem-solving, emotions

Return ONLY the question. NO explanation."""

    CAREER_DISCOVERY_REPORT = """You are an expert career psychologist analyzing quiz responses to find the BEST career sectors for this student.

QUIZ RESPONSES:
{qa_text}

ANALYSIS TASK:
1. Identify TOP 1-3 BROAD SECTORS with fit percentages (must add to 100%)
2. Within each sector, find 2-3 SPECIFIC CAREER PATHS
3. Reveal hidden skills with evidence from answers

BROAD SECTORS TO CHOOSE FROM:
Technology, Healthcare, Business, Engineering, Creative Arts, Education, Science, Law, Social Services, Media & Communications, Hospitality, Sports & Fitness, Environment, Public Service

IMPORTANT RULES:
- Give 1-3 broad sectors with percentages that SUM TO 100%
- If only 1 sector fits → give it 100%
- If 2-3 sectors → split the percentage (e.g., Healthcare 60%, Education 40%)
- Then for EACH sector, list specific career paths

OUTPUT FORMAT (strict markdown):

# Your Career Discovery Results

## Primary Sector Match

**Healthcare** - 100%

*OR if multiple:*

**Healthcare** - 60%
**Education** - 40%

---

## Top Career Sectors & Paths

### 1. Healthcare (100%)

**Why this sector:**
[2-3 sentences with evidence from their answers]

**Specific career paths within Healthcare:**
- **Nursing**: [Why it fits]
- **Physiotherapy**: [Why it fits]
- **Pharmacy**: [Why it fits]

**Degrees to explore:**
- Nursing
- Physiotherapy  
- Pharmacy

---

### 2. Education (40%)

**Why this sector:**
[2-3 sentences with evidence from their answers]

**Specific career paths within Education:**
- **Primary Teacher**: [Why it fits]
- **Educational Psychologist**: [Why it fits]
- **Special Needs Coordinator**: [Why it fits]

**Degrees to explore:**
- Primary Education
- Educational Psychology
- Special Education

---

## Your Hidden Strengths

1. **[Skill Name]**: [Evidence from answer]
2. **[Skill Name]**: [Evidence from answer]
3. **[Skill Name]**: [Evidence from answer]
4. **[Skill Name]**: [Evidence from answer]

## Next Steps

1. Explore degrees in [Primary Sector] using the Degree Picker
2. Research careers: [3 specific job titles]
3. Develop: [2 skills to enhance fit]

## Your Profile Summary
[2-3 sentences describing unique approach/style/values]

---
*Report generated {datetime}*
"""

    SYSTEM_INSTRUCTION_QUESTION = "Return ONLY one creative 15-word question. NO examples. NO career references."
    SYSTEM_INSTRUCTION_REPORT = "You are an expert career psychologist. Give broad sectors with % AND specific paths within them."


class UniversityFinderPrompts:
    """Prompts for International University Search"""

    INTERNATIONAL_SEARCH = """Search the web for universities offering {degree} programs {location_str}.

Find up to 20 universities that match the criteria. For each university provide:
- University official name
- Full program name for {degree}
- Country and city location
- Admission requirements (GPA, test scores, prerequisites if available)
- Annual tuition fees in local currency or EUR
- Application deadlines for 2026/2027 academic year
- QS or THE world ranking if available
- Program duration in years
- Primary language of instruction

Focus on accredited universities with programs taught in English or the local language.{pref_str}

If specific information is not available, use "N/A" for that field.

Return your response as valid JSON with this exact structure:
{{
  "universities": [
    {{
      "name": "University Name",
      "program_name": "Program Name",
      "country": "Country",
      "city": "City",
      "admission_requirements": "Requirements text",
      "tuition_annual": "Amount",
      "application_deadline": "Date",
      "ranking": "QS/THE ranking or N/A",
      "program_duration": "Years",
      "language_of_instruction": "Language"
    }}
  ]
}}

Return ONLY the JSON, no other text or markdown formatting."""
