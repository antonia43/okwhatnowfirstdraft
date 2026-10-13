# FUNCTION CALLING TOOLS FOR STUDENTS

import json
from typing import Optional, List, Dict, Any
from google.genai import types
import pandas as pd
from utils.database import get_saved_universities, load_reports
from pages.university_finder import normalize_text
from services.langfuse_helper import get_user_id, get_session_id
import time
from langfuse.decorators import observe, langfuse_context


# FUNCTION DECLARATIONS

search_universities_tool = types.FunctionDeclaration(
    name="search_saved_universities",
    description="Search through the user's saved universities. Use this when user asks about their saved universities, wants to compare programs, or needs info about specific degrees they've saved.",
    parameters={
        "type": "object",
        "properties": {
            "degree_name": {
                "type": "string",
                "description": "The degree or program to search for (e.g., 'Computer Science', 'Engineering')"
            },
            "country": {
                "type": "string",
                "description": "Filter by country - 'Portugal', 'International', or 'All'",
                "enum": ["Portugal", "International", "All"]
            }
        },
        "required": ["degree_name"]
    }
)

calculate_admission_grade_tool = types.FunctionDeclaration(
    name="calculate_admission_grade",
    description="Calculate the student's admission average (CIF) from their grades. Use when user asks about their chances, admission average, or wants to know if they qualify for universities.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's ID to fetch their grades"
            }
        },
        "required": ["user_id"]
    }
)

search_dges_database_tool = types.FunctionDeclaration(
    name="search_dges_database",
    description="Search the DGES Portuguese university database for specific degrees. Returns universities offering that program with grade requirements and acceptance rates. Use when user wants to find Portuguese universities for a specific degree.",
    parameters={
        "type": "object",
        "properties": {
            "degree_name": {
                "type": "string",
                "description": "The degree to search for (in Portuguese, e.g., 'Engenharia Informática', 'Medicina')"
            },
            "location": {
                "type": "string",
                "description": "Region filter - 'Lisbon', 'Porto', 'Coimbra', or 'All of Portugal'"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default 10)"
            }
        },
        "required": ["degree_name"]
    }
)

get_student_data_tool = types.FunctionDeclaration(
    name="get_student_profile",
    description="Get the student's complete profile including grades, saved universities, and degree preferences. Use when you need context about the student to give personalized advice.",
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


# FUNCTION IMPLEMENTATIONS

# FUNCTION IMPLEMENTATIONS WITH LANGFUSE

@observe(name="search_saved_universities")
def search_saved_universities(degree_name: str, country: str = "All", max_retries: int = 3) -> Dict[str, Any]:
    """Search user's saved universities with retry logic"""
    
    langfuse_context.update_current_observation(
        input={"degree_name": degree_name, "country": country},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            from streamlit import session_state
            user_id = session_state.get("username", "demo_user")

            saved_unis = get_saved_universities(user_id)

            if not saved_unis:
                result = {
                    "success": True,
                    "universities": [],
                    "message": "No saved universities found. Visit University Finder to save some!"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            # Filter by country
            if country == "Portugal":
                saved_unis = [u for u in saved_unis if u.get('type') != 'International']
            elif country == "International":
                saved_unis = [u for u in saved_unis if u.get('type') == 'International']

            # Search by degree name
            normalized_search = normalize_text(degree_name)
            matching_unis = []

            for uni in saved_unis:
                program_normalized = normalize_text(uni.get('program_name', ''))
                if normalized_search in program_normalized:
                    matching_unis.append({
                        "university": uni.get('name', 'Unknown'),
                        "program": uni.get('program_name', 'Unknown'),
                        "location": uni.get('location', 'Unknown'),
                        "type": uni.get('type', 'Unknown'),
                        "grade_required": uni.get('average_grade_required', 'N/A'),
                        "duration": uni.get('duration', 'N/A')
                    })

            result = {
                "success": True,
                "universities": matching_unis,
                "total_saved": len(saved_unis),
                "matching_count": len(matching_unis)
            }
            
            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            
            error_result = {
                "success": False,
                "error": f"Failed to search universities: {str(e)}",
                "universities": []
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    return {"success": False, "error": "Max retries reached", "universities": []}


@observe(name="calculate_admission_grade")
def calculate_admission_grade(user_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Calculate student's admission average with retry logic"""
    
    langfuse_context.update_current_observation(
        input={"user_id": user_id},
        metadata={"max_retries": max_retries}
    )

    for attempt in range(max_retries):
        try:
            grades_reports = load_reports(user_id, "grades")

            if not grades_reports:
                result = {
                    "success": True,
                    "has_grades": False,
                    "message": "No grades found. Complete Grades Analysis first!"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            latest_report = grades_reports[0]
            report_data = json.loads(latest_report['content'])

            final_cif = None
            if "final_cif" in report_data:
                final_cif = report_data["final_cif"]

            if final_cif:
                cif_20 = final_cif / 10.0 if final_cif > 20 else final_cif

                result = {
                    "success": True,
                    "has_grades": True,
                    "cif_200_scale": final_cif,
                    "cif_20_scale": round(cif_20, 2),
                    "weights_used": report_data.get("weights_used", {}),
                    "message": f"Student's admission average: {cif_20:.2f}/20"
                }
                
                langfuse_context.update_current_observation(output=result)
                return result
            else:
                result = {
                    "success": True,
                    "has_grades": True,
                    "message": "Grades available but CIF not calculated yet"
                }
                langfuse_context.update_current_observation(output=result)
                return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            
            error_result = {
                "success": False,
                "error": f"Failed to calculate grade: {str(e)}"
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    return {"success": False, "error": "Max retries reached"}


@observe(name="search_dges_database")
def search_dges_database(degree_name: str, location: str = "All of Portugal", 
                         max_results: int = 10, max_retries: int = 3) -> Dict[str, Any]:
    """Search DGES database with retry logic"""
    
    langfuse_context.update_current_observation(
        input={"degree_name": degree_name, "location": location, "max_results": max_results}
    )

    for attempt in range(max_retries):
        try:
            from streamlit import session_state

            if "universities_df" not in session_state or session_state["universities_df"].empty:
                result = {
                    "success": False,
                    "error": "DGES database not loaded",
                    "universities": []
                }
                langfuse_context.update_current_observation(output=result, level="WARNING")
                return result

            df = session_state["universities_df"].copy()

            normalized_degree = normalize_text(degree_name)
            df["course_name_normalized"] = df["course_name"].apply(normalize_text)
            mask = df["course_name_normalized"].str.contains(normalized_degree, case=False, na=False)

            if location != "All of Portugal":
                mask &= df["region"].eq(location)

            results = df[mask].head(max_results)

            if results.empty:
                result = {
                    "success": True,
                    "universities": [],
                    "message": f"No universities found for '{degree_name}' in {location}"
                }
                langfuse_context.update_current_observation(output=result)
                return result

            universities = []
            for _, row in results.iterrows():
                universities.append({
                    "university": row["institution_name"],
                    "program": row["course_name"],
                    "location": row["region"],
                    "type": row["type"],
                    "last_grade": f"{row['last_grade']:.1f}/20" if pd.notna(row.get('last_grade')) else "N/A",
                    "vacancies": int(row["vacancies"]) if pd.notna(row.get("vacancies")) else "N/A"
                })

            result = {
                "success": True,
                "universities": universities,
                "total_found": len(results)
            }
            
            langfuse_context.update_current_observation(output=result)
            return result

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            
            error_result = {
                "success": False,
                "error": f"Database search failed: {str(e)}",
                "universities": []
            }
            langfuse_context.update_current_observation(
                output=error_result,
                level="ERROR"
            )
            return error_result

    return {"success": False, "error": "Max retries reached", "universities": []}


@observe(name="get_student_profile")
def get_student_profile(user_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Get complete student profile with retry logic"""
    
    langfuse_context.update_current_observation(input={"user_id": user_id})

    for attempt in range(max_retries):
        try:
            profile = {
                "user_id": user_id,
                "has_grades": False,
                "has_degree_reports": False,
                "has_saved_universities": False,
                "admission_average": None,
                "saved_universities_count": 0,
                "degree_reports_count": 0
            }

            grades_reports = load_reports(user_id, "grades")
            if grades_reports:
                profile["has_grades"] = True
                profile["grade_reports_count"] = len(grades_reports)

                try:
                    latest = json.loads(grades_reports[0]['content'])
                    if "final_cif" in latest:
                        cif = latest["final_cif"]
                        profile["admission_average"] = cif / 10.0 if cif > 20 else cif
                except:
                    pass

            degree_reports = load_reports(user_id, "degree")
            if degree_reports:
                profile["has_degree_reports"] = True
                profile["degree_reports_count"] = len(degree_reports)

            saved_unis = get_saved_universities(user_id)
            if saved_unis:
                profile["has_saved_universities"] = True
                profile["saved_universities_count"] = len(saved_unis)

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

    return {"success": False, "error": "Max retries reached"}
    

# FUNCTION DISPATCHER (Mapping function calls to implementations)

FUNCTION_HANDLERS = {
    "search_saved_universities": search_saved_universities,
    "calculate_admission_grade": calculate_admission_grade,
    "search_dges_database": search_dges_database,
    "get_student_profile": get_student_profile
}

def execute_function_call(function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call with error handling"""
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


# TOOLS CONFIGURATION

STUDENT_TOOLS = [
    search_universities_tool,
    calculate_admission_grade_tool,
    search_dges_database_tool,
    get_student_data_tool
]
