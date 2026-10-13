# services/professional_function_tools.py
# FUNCTION CALLING TOOLS FOR PROFESSIONALS WITH LANGFUSE MONITORING

import json
from typing import Optional, List, Dict, Any
from google.genai import types
from utils.database import load_reports
from langfuse import observe
import time


# ============================================================================
# FUNCTION DECLARATIONS (What Gemini can call)
# ============================================================================

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

compare_career_paths_tool = types.FunctionDeclaration(
    name="compare_career_paths",
    description="Compare multiple career paths based on the user's profile. Shows pros/cons, fit score, and which aligns best with their skills and interests. Use when they're deciding between 2-3 career options.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID"
            },
            "career_options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of 2-3 career paths to compare (e.g., ['Data Scientist', 'ML Engineer', 'Product Manager'])"
            }
        },
        "required": ["user_id", "career_options"]
    }
)

calculate_career_readiness_tool = types.FunctionDeclaration(
    name="calculate_career_readiness",
    description="Calculate a readiness score (0-100%) for a target role based on skills, experience, and personality fit. Includes breakdown of what's boosting/lowering the score. Use when they ask if they're ready for a role.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID"
            },
            "target_role": {
                "type": "string",
                "description": "The role to assess readiness for"
            }
        },
        "required": ["user_id", "target_role"]
    }
)


# ============================================================================
# FUNCTION IMPLEMENTATIONS (What actually executes with Langfuse monitoring)
# ============================================================================


@observe(name="analyze_skill_gaps")
def analyze_skill_gaps(user_id: str, target_role: str, max_retries: int = 3) -> Dict[str, Any]:
    """Analyze skill gaps with retry logic and Langfuse monitoring"""

    for attempt in range(max_retries):
        try:
            # Get CV data
            cv_reports = load_reports(user_id, "professional_cv")

            if not cv_reports:
                return {
                    "success": True,
                    "has_data": False,
                    "message": "No CV found. Complete CV Analysis to analyze skill gaps!"
                }

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

            return {
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

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            return {
                "success": False,
                "error": f"Failed to analyze skill gaps: {str(e)}"
            }

    return {"success": False, "error": "Max retries reached"}


@observe(name="get_career_roadmap")
def get_career_roadmap(user_id: str, target_role: str, timeframe: str = "1 year", max_retries: int = 3) -> Dict[str, Any]:
    """Generate career roadmap with retry logic and Langfuse monitoring"""

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

            return {
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
                    f"Land position in {target_role}"
                ],
                "message": f"Career roadmap to {target_role} in {timeframe}"
            }

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue

            return {
                "success": False,
                "error": f"Failed to generate roadmap: {str(e)}"
            }

    return {"success": False, "error": "Max retries reached"}


@observe(name="compare_career_paths")
def compare_career_paths(user_id: str, career_options: List[str], max_retries: int = 3) -> Dict[str, Any]:
    """Compare multiple career paths with retry logic and Langfuse monitoring"""
    
    for attempt in range(max_retries):
        try:
            cv_reports = load_reports(user_id, "professional_cv")
            quiz_reports = load_reports(user_id, "professional_career_quiz")
            
            if not cv_reports:
                return {
                    "success": True,
                    "has_data": False,
                    "message": "No CV found. Complete CV Analysis to compare career paths!"
                }
            
            # Get CV content
            cv_content = cv_reports[0].get('content', '').lower()
            
            # Role skill requirements
            role_requirements = {
                "data scientist": {
                    "skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization"],
                    "personality": ["analytical", "detail-oriented", "problem-solver"],
                    "growth": "High (15-20% annually)",
                    "difficulty": "High"
                },
                "software engineer": {
                    "skills": ["Programming", "Algorithms", "System Design", "Git", "Testing"],
                    "personality": ["logical", "collaborative", "innovative"],
                    "growth": "High (12-18% annually)",
                    "difficulty": "Medium-High"
                },
                "product manager": {
                    "skills": ["Product Strategy", "Stakeholder Management", "Analytics", "UX/UI", "Agile"],
                    "personality": ["leadership", "communication", "strategic"],
                    "growth": "Medium-High (10-15% annually)",
                    "difficulty": "Medium"
                },
                "data analyst": {
                    "skills": ["SQL", "Excel", "Data Visualization", "Statistics", "Python/R"],
                    "personality": ["analytical", "detail-oriented", "communicative"],
                    "growth": "Medium (8-12% annually)",
                    "difficulty": "Medium"
                },
                "ml engineer": {
                    "skills": ["Python", "Deep Learning", "MLOps", "Cloud Services", "Model Deployment"],
                    "personality": ["technical", "innovative", "problem-solver"],
                    "growth": "Very High (18-25% annually)",
                    "difficulty": "Very High"
                },
                "ux designer": {
                    "skills": ["User Research", "Wireframing", "Prototyping", "Figma", "Usability Testing"],
                    "personality": ["creative", "empathetic", "detail-oriented"],
                    "growth": "Medium (8-12% annually)",
                    "difficulty": "Medium"
                }
            }
            
            comparisons = []
            
            for career in career_options:
                career_lower = career.lower()
                
                # Find matching role
                requirements = None
                for role_key, role_data in role_requirements.items():
                    if role_key in career_lower:
                        requirements = role_data
                        break
                
                if not requirements:
                    requirements = {
                        "skills": ["Domain Knowledge", "Communication", "Problem Solving"],
                        "personality": ["adaptable", "motivated"],
                        "growth": "Varies",
                        "difficulty": "Medium"
                    }
                
                # Calculate skill match
                skills_present = sum(1 for skill in requirements["skills"] if skill.lower() in cv_content)
                skill_match = round((skills_present / len(requirements["skills"])) * 100)
                
                # Overall fit score (simple calculation)
                fit_score = min(100, skill_match + 10)  # Add 10 points for having any CV
                
                comparisons.append({
                    "career": career,
                    "fit_score": fit_score,
                    "skill_match": f"{skills_present}/{len(requirements['skills'])} skills",
                    "required_skills": requirements["skills"],
                    "personality_fit": requirements["personality"],
                    "market_growth": requirements["growth"],
                    "difficulty": requirements["difficulty"],
                    "pros": [
                        f"Strong market growth: {requirements['growth']}" if "High" in requirements['growth'] else f"Stable market: {requirements['growth']}",
                        f"You have {skills_present} relevant skills already",
                        "Clear career progression path"
                    ],
                    "cons": [
                        f"Difficulty level: {requirements['difficulty']}",
                        f"Need to learn: {len(requirements['skills']) - skills_present} more skills",
                        "May require additional certifications"
                    ]
                })
            
            # Sort by fit score
            comparisons.sort(key=lambda x: x["fit_score"], reverse=True)
            
            return {
                "success": True,
                "has_data": True,
                "career_options": career_options,
                "comparisons": comparisons,
                "recommendation": comparisons[0]["career"],
                "message": f"Compared {len(career_options)} career paths"
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            
            return {
                "success": False,
                "error": f"Failed to compare careers: {str(e)}"
            }
    
    return {"success": False, "error": "Max retries reached"}


@observe(name="calculate_career_readiness")
def calculate_career_readiness(user_id: str, target_role: str, max_retries: int = 3) -> Dict[str, Any]:
    """Calculate career readiness score with retry logic and Langfuse monitoring"""
    
    for attempt in range(max_retries):
        try:
            cv_reports = load_reports(user_id, "professional_cv")
            quiz_reports = load_reports(user_id, "professional_career_quiz")
            
            if not cv_reports:
                return {
                    "success": True,
                    "has_data": False,
                    "message": "No CV found. Complete CV Analysis to calculate readiness!"
                }
            
            cv_content = cv_reports[0].get('content', '').lower()
            
            # Role requirements (same as above)
            role_skills = {
                "data scientist": ["Python", "Machine Learning", "SQL", "Statistics", "Data Visualization", "Deep Learning"],
                "software engineer": ["Programming", "Algorithms", "System Design", "Git", "Testing", "Databases"],
                "product manager": ["Product Strategy", "Roadmapping", "Stakeholder Management", "Analytics", "UX/UI", "Agile"],
                "data analyst": ["SQL", "Excel", "Data Visualization", "Statistics", "Python/R", "Business Intelligence"],
                "ml engineer": ["Python", "Deep Learning", "MLOps", "Cloud Services", "Model Deployment", "TensorFlow/PyTorch"]
            }
            
            # Find matching role
            target_lower = target_role.lower()
            required_skills = []
            for role, skills in role_skills.items():
                if role in target_lower:
                    required_skills = skills
                    break
            
            if not required_skills:
                required_skills = ["Domain Knowledge", "Communication", "Problem Solving", "Technical Skills", "Leadership", "Adaptability"]
            
            # Calculate scores
            skills_present = [skill for skill in required_skills if skill.lower() in cv_content]
            skills_missing = [skill for skill in required_skills if skill.lower() not in cv_content]
            
            skill_score = round((len(skills_present) / len(required_skills)) * 70)  # 70% weight on skills
            
            # Experience bonus (simple heuristic)
            experience_score = 0
            if "years" in cv_content or "experience" in cv_content:
                experience_score = 20
            elif cv_content.strip():
                experience_score = 10
            
            # Quiz bonus
            quiz_score = 10 if quiz_reports else 0
            
            # Total readiness
            total_score = min(100, skill_score + experience_score + quiz_score)
            
            # Readiness level
            if total_score >= 80:
                readiness_level = "Highly Ready"
                recommendation = f"You're well-prepared for {target_role}! Start applying now."
            elif total_score >= 60:
                readiness_level = "Moderately Ready"
                recommendation = f"You're on the right track. Focus on {skills_missing[0] if skills_missing else 'advanced skills'} to boost readiness."
            elif total_score >= 40:
                readiness_level = "Developing"
                recommendation = f"Build experience with: {', '.join(skills_missing[:3])}. Consider projects or courses."
            else:
                readiness_level = "Early Stage"
                recommendation = f"Significant preparation needed. Start with fundamentals: {', '.join(skills_missing[:2])}."
            
            return {
                "success": True,
                "has_data": True,
                "target_role": target_role,
                "readiness_score": total_score,
                "readiness_level": readiness_level,
                "breakdown": {
                    "skills": skill_score,
                    "experience": experience_score,
                    "personality_fit": quiz_score
                },
                "skills_present": skills_present,
                "skills_missing": skills_missing,
                "recommendation": recommendation,
                "next_steps": [
                    f"Learn: {skills_missing[0]}" if skills_missing else "Refine existing skills",
                    "Build 2-3 portfolio projects" if total_score < 70 else "Polish your portfolio",
                    "Network with professionals in the field",
                    "Apply to entry-level positions" if total_score >= 60 else "Gain more foundational experience"
                ],
                "message": f"Readiness score: {total_score}% for {target_role}"
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            
            return {
                "success": False,
                "error": f"Failed to calculate readiness: {str(e)}"
            }
    
    return {"success": False, "error": "Max retries reached"}


# ============================================================================
# FUNCTION DISPATCHER (Mapping function calls to implementations)
# ============================================================================

FUNCTION_HANDLERS = {
    "analyze_skill_gaps": analyze_skill_gaps,
    "get_career_roadmap": get_career_roadmap,
    "compare_career_paths": compare_career_paths,
    "calculate_career_readiness": calculate_career_readiness
}


@observe(name="execute_professional_function_call")
def execute_function_call(function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call with error handling and Langfuse monitoring"""

    try:
        if function_name not in FUNCTION_HANDLERS:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }

        handler = FUNCTION_HANDLERS[function_name]
        result = handler(**function_args)

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Function execution failed: {str(e)}"
        }


# ============================================================================
# TOOLS CONFIGURATION (For Gemini)
# ============================================================================

PROFESSIONAL_TOOLS = types.Tool(function_declarations=[
    analyze_skill_gaps_tool,
    get_career_roadmap_tool,
    compare_career_paths_tool,
    calculate_career_readiness_tool
])
