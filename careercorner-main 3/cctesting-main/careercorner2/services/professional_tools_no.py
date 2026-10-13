# services/professional_function_tools.py
# FUNCTION CALLING TOOLS FOR PROFESSIONALS WITH LANGFUSE MONITORING

import json
from typing import Optional, List, Dict, Any
from google.genai import types
from utils.database import load_reports
from langfuse.decorators import observe, langfuse_context
import time


# ============================================================================
# FUNCTION DECLARATIONS (What Gemini can call)
# ============================================================================

get_cv_analysis_tool = types.FunctionDeclaration(
    name="get_cv_analysis",
    description="Get the professional's CV analysis including skills, experience, and recommendations. Use when you need to reference their background, skills, or work history.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID to fetch their CV"
            }
        },
        "required": ["user_id"]
    }
)

get_career_quiz_results_tool = types.FunctionDeclaration(
    name="get_career_quiz_results",
    description="Get the professional's career quiz results including personality type, career interests, and recommended paths. Use when advising on career direction or job fit.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID to fetch their quiz results"
            }
        },
        "required": ["user_id"]
    }
)

analyze_skill_gaps_tool = types.FunctionDeclaration(
    name="analyze_skill_gaps",
    description="Analyze skill gaps between the user's current CV skills and their target role. Returns missing skills and learning recommendations. Use when advising on career transitions or upskilling.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID"
            },
            "target_role": {
                "type": "string",
                "description": "The job role they're targeting (e.g., 'Data Scientist', 'Product Manager')"
            }
        },
        "required": ["user_id", "target_role"]
    }
)

get_career_roadmap_tool = types.FunctionDeclaration(
    name="get_career_roadmap",
    description="Generate a personalized career roadmap based on their current position and target role. Use when they ask about career progression or next steps.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID"
            },
            "target_role": {
                "type": "string",
                "description": "The job role they're aiming for"
            },
            "timeframe": {
                "type": "string",
                "description": "Timeframe for the roadmap (e.g., '6 months', '1 year', '2 years')"
            }
        },
        "required": ["user_id", "target_role"]
    }
)

get_professional_profile_tool = types.FunctionDeclaration(
    name="get_professional_profile",
    description="Get complete professional profile including CV, quiz results, and career data. Use when you need comprehensive context about the professional.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID"
            }
        },
        "required": ["user_id"]
    }
)


# ============================================================================
# FUNCTION IMPLEMENTATIONS (What actually executes with Langfuse monitoring)
# ============================================================================

@observe(name="get_cv_analysis")
def get_cv_analysis(user_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Get CV analysis with retry logic and Langfuse monitoring"""

    langfuse_context.update_current_observation(
        input={"user_id": user_id},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            cv_reports = load_reports(user_id, "professional_cv")

            if not cv_reports:
                result = {
                    "success": True,
                    "has_cv": False,
                    "message": "No CV analysis found. Complete CV Analysis first!"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            latest_cv = cv_reports[0]
            cv_content = latest_cv.get('content', '')

            # Try to parse if it's JSON
            try:
                cv_data = json.loads(cv_content)
            except:
                cv_data = {"raw_content": cv_content}

            result = {
                "success": True,
                "has_cv": True,
                "cv_title": latest_cv.get('title', 'Untitled CV'),
                "cv_data": cv_data,
                "total_cvs": len(cv_reports),
                "message": f"CV analysis available: {latest_cv.get('title', 'Untitled')}"
            }

            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            error_result = {
                "success": False,
                "error": f"Failed to load CV: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    error_result = {"success": False, "error": "Max retries reached"}
    langfuse_context.update_current_observation(output=error_result, level="ERROR")
    return error_result


@observe(name="get_career_quiz_results")
def get_career_quiz_results(user_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Get career quiz results with retry logic and Langfuse monitoring"""

    langfuse_context.update_current_observation(
        input={"user_id": user_id},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            quiz_reports = load_reports(user_id, "professional_career_quiz")

            if not quiz_reports:
                result = {
                    "success": True,
                    "has_quiz": False,
                    "message": "No career quiz results found. Complete Career Quiz first!"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            latest_quiz = quiz_reports[0]
            quiz_content = latest_quiz.get('content', '')

            try:
                quiz_data = json.loads(quiz_content)
            except:
                quiz_data = {"raw_content": quiz_content}

            result = {
                "success": True,
                "has_quiz": True,
                "quiz_title": latest_quiz.get('title', 'Untitled Quiz'),
                "quiz_data": quiz_data,
                "total_quizzes": len(quiz_reports),
                "message": f"Career quiz results available: {latest_quiz.get('title', 'Untitled')}"
            }

            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            error_result = {
                "success": False,
                "error": f"Failed to load quiz results: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    error_result = {"success": False, "error": "Max retries reached"}
    langfuse_context.update_current_observation(output=error_result, level="ERROR")
    return error_result


@observe(name="analyze_skill_gaps")
def analyze_skill_gaps(user_id: str, target_role: str, max_retries: int = 3) -> Dict[str, Any]:
    """Analyze skill gaps with retry logic and Langfuse monitoring"""

    langfuse_context.update_current_observation(
        input={"user_id": user_id, "target_role": target_role},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            # Get CV data
            cv_reports = load_reports(user_id, "professional_cv")

            if not cv_reports:
                result = {
                    "success": True,
                    "has_data": False,
                    "message": "No CV found. Complete CV Analysis to analyze skill gaps!"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            latest_cv = cv_reports[0]
            cv_content = latest_cv.get('content', '')

            # Common skill requirements for different roles
            role_skills = {
                "data scientist": ["Python", "Machine Learning", "SQL", "Statistics", "Data Visualization", "Deep Learning"],
                "software engineer": ["Programming", "Algorithms", "System Design", "Git", "Testing", "Databases"],
                "product manager": ["Product Strategy", "Roadmapping", "Stakeholder Management", "Analytics", "UX/UI", "Agile"],
                "marketing manager": ["Digital Marketing", "SEO/SEM", "Content Strategy", "Analytics", "Social Media", "Campaign Management"],
                "data analyst": ["SQL", "Excel", "Data Visualization", "Statistics", "Python/R", "Business Intelligence"],
                "ux designer": ["User Research", "Wireframing", "Prototyping", "Figma/Sketch", "Usability Testing", "Information Architecture"]
            }

            # Find matching role skills
            target_lower = target_role.lower()
            required_skills = []
            for role, skills in role_skills.items():
                if role in target_lower:
                    required_skills = skills
                    break

            if not required_skills:
                required_skills = ["Domain Knowledge", "Communication", "Problem Solving", "Technical Skills", "Leadership"]

            # Simple gap analysis (check if skills mentioned in CV)
            cv_lower = cv_content.lower()
            missing_skills = [skill for skill in required_skills if skill.lower() not in cv_lower]
            existing_skills = [skill for skill in required_skills if skill.lower() in cv_lower]

            result = {
                "success": True,
                "has_data": True,
                "target_role": target_role,
                "required_skills": required_skills,
                "existing_skills": existing_skills,
                "missing_skills": missing_skills,
                "gap_percentage": round((len(missing_skills) / len(required_skills)) * 100, 1) if required_skills else 0,
                "recommendations": [
                    f"Focus on learning: {', '.join(missing_skills[:3])}" if missing_skills else "You have most required skills!",
                    "Consider online courses (Coursera, Udemy, edX)",
                    "Build projects to demonstrate skills",
                    "Update your CV with specific examples"
                ],
                "message": f"Skill gap analysis for {target_role} complete"
            }

            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            error_result = {
                "success": False,
                "error": f"Failed to analyze skill gaps: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    error_result = {"success": False, "error": "Max retries reached"}
    langfuse_context.update_current_observation(output=error_result, level="ERROR")
    return error_result


@observe(name="get_career_roadmap")
def get_career_roadmap(user_id: str, target_role: str, timeframe: str = "1 year", max_retries: int = 3) -> Dict[str, Any]:
    """Generate career roadmap with retry logic and Langfuse monitoring"""

    langfuse_context.update_current_observation(
        input={"user_id": user_id, "target_role": target_role, "timeframe": timeframe},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            cv_reports = load_reports(user_id, "professional_cv")
            quiz_reports = load_reports(user_id, "professional_career_quiz")

            has_cv = len(cv_reports) > 0 if cv_reports else False
            has_quiz = len(quiz_reports) > 0 if quiz_reports else False

            # Generate roadmap phases
            if "6 month" in timeframe.lower():
                phases = [
                    {"phase": "Month 1-2", "focus": "Skill Assessment & Learning Plan", "actions": ["Identify skill gaps", "Enroll in 1-2 key courses", "Start building portfolio"]},
                    {"phase": "Month 3-4", "focus": "Skill Development", "actions": ["Complete courses", "Build 2-3 projects", "Network on LinkedIn"]},
                    {"phase": "Month 5-6", "focus": "Job Search & Application", "actions": ["Update CV", "Apply to positions", "Practice interviews"]}
                ]
            elif "2 year" in timeframe.lower():
                phases = [
                    {"phase": "Months 1-6", "focus": "Foundation Building", "actions": ["Complete certifications", "Build strong portfolio", "Gain experience"]},
                    {"phase": "Months 7-12", "focus": "Intermediate Growth", "actions": ["Take on complex projects", "Develop leadership skills", "Expand network"]},
                    {"phase": "Months 13-18", "focus": "Advanced Development", "actions": ["Specialize in niche area", "Mentor others", "Build personal brand"]},
                    {"phase": "Months 19-24", "focus": "Transition & Positioning", "actions": ["Target dream companies", "Negotiate offers", "Make strategic move"]}
                ]
            else:  # Default 1 year
                phases = [
                    {"phase": "Month 1-3", "focus": "Skill Assessment & Learning", "actions": ["Complete skill gap analysis", "Enroll in key courses", "Start portfolio projects"]},
                    {"phase": "Month 4-6", "focus": "Building Experience", "actions": ["Complete 3-5 projects", "Contribute to open source", "Network actively"]},
                    {"phase": "Month 7-9", "focus": "Career Positioning", "actions": ["Update CV and LinkedIn", "Build personal brand", "Start applications"]},
                    {"phase": "Month 10-12", "focus": "Job Search & Transition", "actions": ["Apply strategically", "Interview preparation", "Negotiate and transition"]}
                ]

            result = {
                "success": True,
                "target_role": target_role,
                "timeframe": timeframe,
                "has_cv": has_cv,
                "has_quiz": has_quiz,
                "roadmap_phases": phases,
                "key_milestones": [
                    f"Learn core {target_role} skills",
                    "Build portfolio demonstrating expertise",
                    "Expand professional network",
                    "Land position in {target_role}"
                ],
                "message": f"Career roadmap to {target_role} in {timeframe}"
            }

            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            error_result = {
                "success": False,
                "error": f"Failed to generate roadmap: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    error_result = {"success": False, "error": "Max retries reached"}
    langfuse_context.update_current_observation(output=error_result, level="ERROR")
    return error_result


@observe(name="get_professional_profile")
def get_professional_profile(user_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Get complete professional profile with retry logic and Langfuse monitoring"""

    langfuse_context.update_current_observation(input={"user_id": user_id})

    for attempt in range(max_retries):
        try:
            profile = {
                "user_id": user_id,
                "has_cv": False,
                "has_quiz": False,
                "cv_count": 0,
                "quiz_count": 0,
                "cv_summary": None,
                "quiz_summary": None
            }

            cv_reports = load_reports(user_id, "professional_cv")
            if cv_reports:
                profile["has_cv"] = True
                profile["cv_count"] = len(cv_reports)
                profile["cv_summary"] = cv_reports[0].get('title', 'Untitled CV')

            quiz_reports = load_reports(user_id, "professional_career_quiz")
            if quiz_reports:
                profile["has_quiz"] = True
                profile["quiz_count"] = len(quiz_reports)
                profile["quiz_summary"] = quiz_reports[0].get('title', 'Untitled Quiz')

            result = {
                "success": True,
                "profile": profile
            }

            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            error_result = {
                "success": False,
                "error": f"Failed to load profile: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    error_result = {"success": False, "error": "Max retries reached"}
    langfuse_context.update_current_observation(output=error_result, level="ERROR")
    return error_result


# ============================================================================
# FUNCTION DISPATCHER (Mapping function calls to implementations)
# ============================================================================

FUNCTION_HANDLERS = {
    "get_cv_analysis": get_cv_analysis,
    "get_career_quiz_results": get_career_quiz_results,
    "analyze_skill_gaps": analyze_skill_gaps,
    "get_career_roadmap": get_career_roadmap,
    "get_professional_profile": get_professional_profile
}


@observe(name="execute_professional_function_call")
def execute_function_call(function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call with error handling and Langfuse monitoring"""

    langfuse_context.update_current_observation(
        input={"function_name": function_name, "function_args": function_args}
    )

    try:
        if function_name not in FUNCTION_HANDLERS:
            result = {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }
            langfuse_context.update_current_observation(output=result, level="ERROR")
            return result

        handler = FUNCTION_HANDLERS[function_name]
        result = handler(**function_args)

        langfuse_context.update_current_observation(output=result)
        return result

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Function execution failed: {str(e)}"
        }
        langfuse_context.update_current_observation(output=error_result, level="ERROR")
        return error_result


# ============================================================================
# TOOLS CONFIGURATION (For Gemini)
# ============================================================================

PROFESSIONAL_TOOLS = types.Tool(function_declarations=[
    get_cv_analysis_tool,
    get_career_quiz_results_tool,
    analyze_skill_gaps_tool,
    get_career_roadmap_tool,
    get_professional_profile_tool
])
