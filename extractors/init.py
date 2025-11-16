"""
Пакет для извлечения структурированной информации из текста.
"""

from extractors.requirements_extractor import (
    RequirementsExtractor,
    SkillsBasedRequirementsExtractor
)
from extractors.responsibilities_extractor import ResponsibilitiesExtractor

__all__ = [
    'RequirementsExtractor',
    'SkillsBasedRequirementsExtractor',
    'ResponsibilitiesExtractor'
]
