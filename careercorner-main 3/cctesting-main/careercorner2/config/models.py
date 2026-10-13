# config/models.py
"""
Centralized model configuration for Career Corner
All model names, temperatures, and settings in one place
"""

class ModelConfig:
    """Model names and settings"""

    # ========== MODEL NAMES ==========
    GEMINI_FLASH_2_0 = "gemini-2.0-flash-001"
    GEMINI_FLASH_2_5 = "gemini-2.5-flash"

    # ========== TEMPERATURE PRESETS ==========
    TEMP_DETERMINISTIC = 0.1   # For extraction, parsing (CV extraction, grade extraction)
    TEMP_PRECISE = 0.2         # For structured output (degree questions)
    TEMP_FOCUSED = 0.3         # For analysis with facts (CV feedback, quiz analysis)
    TEMP_BALANCED = 0.4        # For conversational (dashboard chats, polish CV)
    TEMP_MODERATE = 0.5        # For search/recommendations (university search, interview questions)
    TEMP_CREATIVE_MID = 0.6    # For reports (interview feedback, career reports)
    TEMP_CREATIVE_HIGH = 0.7   # For cover letters, function calling chats
    TEMP_VERY_CREATIVE = 0.9   # For adaptive questions (career quiz)

    # ========== MODULE-SPECIFIC CONFIGS ==========

    # Career Growth Quiz (Professional)
    CAREER_QUIZ_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "question_generation_temp": TEMP_FOCUSED,
        "analysis_temp": TEMP_FOCUSED
    }

    # CV Analysis
    CV_ANALYSIS_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "extraction_temp": TEMP_DETERMINISTIC,
        "feedback_temp": TEMP_FOCUSED
    }

    # CV Builder
    CV_BUILDER_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "polish_temp": TEMP_BALANCED,
        "cover_letter_temp": TEMP_CREATIVE_HIGH
    }

    # Degree Picker
    DEGREE_PICKER_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "question_temp": TEMP_PRECISE,
        "portugal_report_temp": TEMP_BALANCED,
        "international_report_temp": TEMP_CREATIVE_MID,
        "extraction_temp": TEMP_DETERMINISTIC
    }

    # Grades Analysis
    GRADES_ANALYSIS_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "extraction_temp": TEMP_DETERMINISTIC
    }

    # Interview Simulator
    INTERVIEW_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "question_generation_temp": TEMP_MODERATE,
        "feedback_temp": TEMP_CREATIVE_MID
    }

    # Dashboard Chats (Student & Professional)
    DASHBOARD_CHAT_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "temp": TEMP_BALANCED
    }

    # Resources Chat (with function calling)
    RESOURCES_CHAT_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "temp": TEMP_CREATIVE_HIGH
    }

    # Student Career Quiz
    STUDENT_CAREER_QUIZ_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "adaptive_question_temp": TEMP_VERY_CREATIVE,
        "report_temp": TEMP_CREATIVE_MID
    }

    # University Finder (International Search)
    UNIVERSITY_FINDER_CONFIG = {
        "model": GEMINI_FLASH_2_5,
        "search_temp": TEMP_MODERATE
    }
