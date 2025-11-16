"""
Модуль с абстрактными интерфейсами для всех компонентов системы.
Следует принципу Dependency Inversion (SOLID).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


class IVacancySearcher(ABC):
    """Интерфейс для поиска вакансий."""

    @abstractmethod
    def search(
            self,
            query: str,
            area: int = 1,
            max_pages: int = 20
    ) -> List[Dict]:
        """
        Поиск вакансий по запросу.

        Args:
            query: Название должности
            area: Код региона
            max_pages: Максимальное количество страниц

        Returns:
            Список вакансий с краткой информацией
        """
        pass


class IVacancyDetailsFetcher(ABC):
    """Интерфейс для получения детальной информации о вакансиях."""

    @abstractmethod
    def fetch_details(self, vacancy_ids: List[str]) -> List[Dict]:
        """
        Получение детальной информации по списку ID вакансий.

        Args:
            vacancy_ids: Список идентификаторов вакансий

        Returns:
            Список вакансий с детальной информацией
        """
        pass


class IDataSaver(ABC):
    """Интерфейс для сохранения данных."""

    @abstractmethod
    def save(self, data: Any, filepath: str) -> None:
        """
        Сохранение данных в файл.

        Args:
            data: Данные для сохранения
            filepath: Путь к файлу
        """
        pass


class IVacancyAnalyzer(ABC):
    """Интерфейс для анализа вакансий."""

    @abstractmethod
    def extract_data(self) -> pd.DataFrame:
        """Извлечение и структурирование данных."""
        pass

    @abstractmethod
    def analyze_skills(self) -> pd.DataFrame:
        """Анализ навыков."""
        pass

    @abstractmethod
    def analyze_requirements(
            self,
            tech_keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Анализ требований."""
        pass

    @abstractmethod
    def get_salary_stats(self) -> Dict:
        """Статистика по зарплатам."""
        pass


class IVacancyVisualizer(ABC):
    """Интерфейс для визуализации результатов."""

    @abstractmethod
    def visualize(
            self,
            analyzer: IVacancyAnalyzer,
            output_dir: str,
            show_plots: bool = False
    ) -> None:
        """
        Создание визуализаций.

        Args:
            analyzer: Анализатор данных
            output_dir: Директория для сохранения
            show_plots: Показывать ли графики
        """
        pass
