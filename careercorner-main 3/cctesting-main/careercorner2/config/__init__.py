# config/__init__.py
"""
Centralized configuration for Career Corner
Import models, prompts, and schemas from a single place
"""

from .models import ModelConfig
from .prompts import (
    CareerQuizPrompts,
    CVAnalysisPrompts,
    CVBuilderPrompts,
    DegreePickerPrompts,
    GradesAnalysisPrompts,
    InterviewSimulatorPrompts,
    DashboardChatPrompts,
    ResourcesChatPrompts,
    StudentCareerQuizPrompts,
    UniversityFinderPrompts
)
from .schemas import (
    CVSchemas,
    FallbackQuestions,
    DropdownOptions
)

__all__ = [
    'ModelConfig',
    'CareerQuizPrompts',
    'CVAnalysisPrompts',
    'CVBuilderPrompts',
    'DegreePickerPrompts',
    'GradesAnalysisPrompts',
    'InterviewSimulatorPrompts',
    'DashboardChatPrompts',
    'ResourcesChatPrompts',
    'StudentCareerQuizPrompts',
    'UniversityFinderPrompts',
    'CVSchemas',
    'FallbackQuestions',
    'DropdownOptions'
]
