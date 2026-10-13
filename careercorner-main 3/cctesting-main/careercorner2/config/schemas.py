# config/schemas.py
"""
Centralized schemas, fallback data, and structured configs
"""

class CVSchemas:
    """CV extraction schemas"""

    EXTRACTION_SCHEMA = {
        "full_name": "What is the full name of the candidate?",
        "email": "What is the candidate's email address?",
        "phone": "What is the candidate's phone number?",
        "education": "List the candidate's education background.",
        "experience": "Summarize the candidate's professional experience.",
        "skills": "List the key technical and soft skills mentioned.",
        "languages": "Which languages does the candidate know?",
        "summary": "Summarize this CV in 3 sentences."
    }


class FallbackQuestions:
    """Fallback questions when AI generation fails"""

    CAREER_QUIZ_EXPERIENCE = [
        {
            "question": "How much do you enjoy working under pressure and tight deadlines?",
            "aspect": "pressure",
            "type": "slider",
            "scale": {"0": "Very stressful", "50": "OK", "100": "I thrive on it"},
        },
        {
            "question": "What kind of tasks do you usually enjoy more?",
            "aspect": "task_type",
            "type": "multiple_choice",
            "options": [
                "Working with people",
                "Analytical/technical tasks",
                "Creative work",
                "Organizing and planning",
                "Hands-on/manual work",
            ],
        },
        {
            "question": "How comfortable are you with customer or client interaction?",
            "aspect": "customer",
            "type": "slider",
            "scale": {"0": "Very uncomfortable", "50": "Neutral", "100": "Really enjoy it"},
        },
        {
            "question": "What do you usually dislike most in a job or project?",
            "aspect": "dislikes",
            "type": "multiple_choice",
            "options": [
                "Repetitive tasks",
                "Lack of autonomy",
                "Too much pressure",
                "Poor work-life balance",
                "Unclear expectations",
            ],
        },
        {
            "question": "How much do you prefer teamwork vs. working independently?",
            "aspect": "teamwork",
            "type": "slider",
            "scale": {"0": "Mostly alone", "50": "Balanced", "100": "Mostly in teams"},
        },
        {
            "question": "What kind of environment do you imagine yourself in?",
            "aspect": "environment",
            "type": "multiple_choice",
            "options": [
                "Fast-paced startup",
                "Structured corporate",
                "Remote/flexible",
                "Creative studio",
                "Research/academic",
            ],
        },
    ]

    CAREER_QUIZ_SOFTSKILLS = [
        {
            "question": "How comfortable are you in leadership roles?",
            "aspect": "leadership",
            "type": "slider",
            "scale": {"0": "Prefer to follow", "50": "Either is fine", "100": "Natural leader"},
        },
        {
            "question": "Which communication style do you prefer most?",
            "aspect": "communication",
            "type": "multiple_choice",
            "options": ["Face-to-face", "Written", "Presentations", "One-on-one", "Group discussions"],
        },
        {
            "question": "How do you usually react to unexpected changes?",
            "aspect": "adaptability",
            "type": "slider",
            "scale": {"0": "Very uncomfortable", "50": "I adapt with effort", "100": "I enjoy change"},
        },
        {
            "question": "How do you normally solve complex problems?",
            "aspect": "problem_solving",
            "type": "multiple_choice",
            "options": [
                "Data and analysis",
                "Creative brainstorming",
                "Asking others",
                "Trial and error",
                "Researching deeply",
            ],
        },
        {
            "question": "How well do you handle stressful situations?",
            "aspect": "stress",
            "type": "slider",
            "scale": {"0": "Easily overwhelmed", "50": "Manageable", "100": "Stay calm and focused"},
        },
        {
            "question": "How do you prefer to learn new skills?",
            "aspect": "learning",
            "type": "multiple_choice",
            "options": [
                "Hands-on practice",
                "Reading",
                "Watching tutorials",
                "Mentoring",
                "Experimenting on my own",
            ],
        },
    ]

    INTERVIEW_FALLBACK = [
        {
            "question": "Tell me about yourself and your background.",
            "category": "Introduction",
            "tips": "Keep it to 2–3 minutes, focus on relevant experience.",
        },
        {
            "question": "Tell me about a time you faced a significant challenge at work. How did you handle it?",
            "category": "Behavioral",
            "tips": "Use the STAR method.",
        },
        {
            "question": "What are your greatest strengths?",
            "category": "Strengths/Weaknesses",
            "tips": "Pick 2–3 relevant strengths with examples.",
        },
        {
            "question": "Where do you see yourself in 5 years?",
            "category": "Career Goals",
            "tips": "Show ambition but be realistic.",
        },
        {
            "question": "Why do you want to work here?",
            "category": "Company Fit",
            "tips": "Research the company and be specific.",
        },
    ]

    STUDENT_CAREER_QUIZ_FALLBACK = [
        "What's the most satisfying 'small win' you've had recently?",
        "Describe a time you broke a rule for a good reason.",
        "You wake up with a new talent. What is it?",
        "Perfect day starts with what sound/smell/feeling?",
        "What object would you save if your house was flooding?",
        "Stranded on island: 3 things you grab first?",
        "Memory that still makes you laugh out loud?",
        "What question do you hate being asked?",
        "You're invisible for one day. First thing you do?",
        "Childhood game you wish adults still played?",
    ]


class DropdownOptions:
    """Dropdown options for UI components"""

    COMMON_DEGREES_PORTUGUESE = [
        "Informática",
        "Engenharia",
        "Gestão",
        "Enfermagem",
        "Psicologia",
        "Medicina",
        "Direito",
        "Ciências",
        "Comunicação",
        "Design",
        "Arquitetura",
        "Turismo",
        "Educação",
        "Desporto",
        "Biotecnologia",
    ]

    COMMON_DEGREES_INTERNATIONAL = [
        "Computer Science",
        "Data Science",
        "Engineering",
        "Business Administration",
        "Psychology",
        "Medicine",
        "Law",
        "Economics",
        "Architecture",
        "Biology",
    ]

    INTERVIEW_FOCUS_AREAS = [
        "Behavioral",
        "Technical",
        "Situational",
        "Strengths/Weaknesses",
        "Career Goals"
    ]

    CAREER_SECTORS = [
        "Technology",
        "Healthcare",
        "Business",
        "Engineering",
        "Creative",
        "Other"
    ]

    COUNTRIES_INTERNATIONAL = [
        "Any Country",
        "United States",
        "United Kingdom",
        "Germany",
        "Netherlands",
        "Canada",
        "Australia",
        "France",
        "Spain",
        "Italy",
        "Sweden",
        "Denmark",
        "Switzerland",
        "Austria",
        "Belgium",
        "Czech Republic",
        "Poland",
        "Ireland",
        "Norway",
        "Finland",
        "Other"
    ]

    CITIES_INTERNATIONAL = [
        "Any City",
        "London",
        "Berlin",
        "Amsterdam",
        "Paris",
        "Barcelona",
        "Munich",
        "Copenhagen",
        "Stockholm",
        "Vienna",
        "Prague",
        "Dublin",
        "Oslo",
        "Helsinki",
        "Other"
    ]
