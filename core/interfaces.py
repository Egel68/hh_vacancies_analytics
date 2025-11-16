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
            max_pages: int = 20,
            max_vacancies: Optional[int] = None
    ) -> List[Dict]:
        """
        Поиск вакансий по запросу.

        Args:
            query: Название должности
            area: Код региона
            max_pages: Максимальное количество страниц
            max_vacancies: Максимальное количество вакансий (None = все)

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

    @abstractmethod
    def analyze_by_company(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по компаниям.

        Args:
            top_n: Количество топовых компаний

        Returns:
            DataFrame с компаниями и количеством вакансий
        """
        pass

    @abstractmethod
    def analyze_by_schedule(self) -> pd.DataFrame:
        """
        Группировка вакансий по формату работы.

        Returns:
            DataFrame с форматами работы и их количеством
        """
        pass

    @abstractmethod
    def analyze_by_metro(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по станциям метро.

        Args:
            top_n: Количество топовых станций

        Returns:
            DataFrame со станциями метро и количеством вакансий
        """
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


# ========== НОВЫЕ ИНТЕРФЕЙСЫ ДЛЯ ОБРАБОТКИ ОПИСАНИЙ ==========


class ITextCleaner(ABC):
    """Интерфейс для очистки текста от HTML и лишних символов."""

    @abstractmethod
    def clean(self, raw_text: str) -> str:
        """
        Очистка текста.

        Args:
            raw_text: Сырой текст (HTML)

        Returns:
            Очищенный текст
        """
        pass


class ITextSectionExtractor(ABC):
    """Интерфейс для извлечения секций из текста."""

    @abstractmethod
    def extract(self, text: str) -> List[str]:
        """
        Извлечение релевантных секций из текста.

        Args:
            text: Очищенный текст

        Returns:
            Список извлеченных элементов
        """
        pass


class IDescriptionProcessor(ABC):
    """Интерфейс для комплексной обработки описаний вакансий."""

    @abstractmethod
    def process_vacancies(
            self,
            vacancies: List[Dict]
    ) -> pd.DataFrame:
        """
        Обработка описаний всех вакансий.

        Args:
            vacancies: Список вакансий с полем description

        Returns:
            DataFrame с извлеченными требованиями и задачами
        """
        pass

    @abstractmethod
    def get_requirements_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ требований.

        Returns:
            DataFrame с частотой встречаемости требований
        """
        pass

    @abstractmethod
    def get_responsibilities_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ задач/обязанностей.

        Returns:
            DataFrame с частотой встречаемости задач
        """
        pass

    @abstractmethod
    def get_detailed_vacancy_data(self) -> List[Dict]:
        """
        Получение детальных данных по каждой вакансии.

        Returns:
            Список словарей с детальной информацией
        """
        pass
