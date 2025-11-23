"""
Модуль с абстрактными интерфейсами для всех компонентов системы.

Следует принципу Dependency Inversion (SOLID) - зависимость от абстракций.
Следует принципу Interface Segregation - разделение интерфейсов по функциональности.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd


# ==================== ПОИСК И ПОЛУЧЕНИЕ ДАННЫХ ====================

class IVacancySearcher(ABC):
    """
    Интерфейс для поиска вакансий.

    Определяет контракт для компонентов, выполняющих поиск вакансий
    на различных платформах.
    """

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
            query: Название должности или ключевые слова
            area: Код региона поиска
            max_pages: Максимальное количество страниц для парсинга
            max_vacancies: Максимальное количество вакансий (None = все)

        Returns:
            List[Dict]: Список вакансий с краткой информацией
        """
        pass


class IVacancyDetailsFetcher(ABC):
    """
    Интерфейс для получения детальной информации о вакансиях.

    Определяет контракт для компонентов, получающих полную информацию
    о вакансиях по их идентификаторам.
    """

    @abstractmethod
    def fetch_details(self, vacancy_ids: List[str]) -> List[Dict]:
        """
        Получение детальной информации по списку ID вакансий.

        Args:
            vacancy_ids: Список идентификаторов вакансий

        Returns:
            List[Dict]: Список вакансий с детальной информацией
        """
        pass

    @abstractmethod
    def get_error_statistics(self) -> Dict:
        """Возвращает статистику по ошибкам"""
        pass


# ==================== СОХРАНЕНИЕ ДАННЫХ ====================

# ==================== СОХРАНЕНИЕ ДАННЫХ ====================

# ==================== СОХРАНЕНИЕ ДАННЫХ ====================

class IDataSaver(ABC):
    """
    Интерфейс для сохранения данных.

    Определяет контракт для компонентов, сохраняющих данные
    в различных форматах.
    """

    @abstractmethod
    def save(self, data: Any, filepath: str) -> None:
        """
        Сохранение данных в файл.

        Args:
            data: Данные для сохранения
            filepath: Путь к файлу для сохранения
        """
        pass


# ==================== АНАЛИЗ ДАННЫХ ====================

class IVacancyAnalyzer(ABC):
    """
    Интерфейс для анализа вакансий.

    Определяет контракт для компонентов, выполняющих различные
    виды анализа данных о вакансиях.
    """

    @abstractmethod
    def extract_data(self) -> pd.DataFrame:
        """
        Извлечение и структурирование данных.

        Returns:
            pd.DataFrame: Структурированные данные о вакансиях
        """
        pass

    @abstractmethod
    def analyze_skills(self) -> pd.DataFrame:
        """
        Анализ навыков, упомянутых в вакансиях.

        Returns:
            pd.DataFrame: Навыки с частотой упоминания
        """
        pass

    @abstractmethod
    def analyze_requirements(
            self,
            tech_keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Анализ требований к кандидатам.

        Args:
            tech_keywords: Список ключевых слов для анализа

        Returns:
            pd.DataFrame: Требования с частотой упоминания
        """
        pass

    @abstractmethod
    def get_salary_stats(self) -> Dict:
        """
        Статистика по зарплатам.

        Returns:
            Dict: Словарь со статистическими показателями
        """
        pass

    @abstractmethod
    def analyze_by_company(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по компаниям.

        Args:
            top_n: Количество топовых компаний

        Returns:
            pd.DataFrame: Компании с количеством вакансий
        """
        pass

    @abstractmethod
    def analyze_by_schedule(self) -> pd.DataFrame:
        """
        Группировка вакансий по формату работы.

        Returns:
            pd.DataFrame: Форматы работы с их количеством
        """
        pass

    @abstractmethod
    def analyze_by_metro(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по станциям метро.

        Args:
            top_n: Количество топовых станций

        Returns:
            pd.DataFrame: Станции метро с количеством вакансий
        """
        pass


# ==================== ВИЗУАЛИЗАЦИЯ ====================

class IVacancyVisualizer(ABC):
    """
    Интерфейс для визуализации результатов анализа.

    Определяет контракт для компонентов, создающих графики
    и диаграммы на основе проанализированных данных.
    """

    @abstractmethod
    def visualize(
            self,
            analyzer: IVacancyAnalyzer,
            output_dir: str,
            show_plots: bool = False
    ) -> None:
        """
        Создание визуализаций на основе данных анализатора.

        Args:
            analyzer: Анализатор с данными
            output_dir: Директория для сохранения графиков
            show_plots: Показывать ли графики в окне
        """
        pass


# ==================== ОБРАБОТКА ТЕКСТА ====================

class ITextCleaner(ABC):
    """
    Интерфейс для очистки текста от HTML и нормализации.

    Определяет контракт для компонентов, выполняющих очистку
    и нормализацию текстовых данных.
    """

    @abstractmethod
    def clean(self, raw_text: str) -> str:
        """
        Очистка текста от HTML и нормализация.

        Args:
            raw_text: Сырой текст (может содержать HTML)

        Returns:
            str: Очищенный и нормализованный текст
        """
        pass


class ITextSectionExtractor(ABC):
    """
    Интерфейс для извлечения секций из текста.

    Определяет контракт для компонентов, извлекающих определенные
    секции (требования, обязанности и т.д.) из текста вакансий.
    """

    @abstractmethod
    def extract(self, text: str) -> List[str]:
        """
        Извлечение релевантных секций из текста.

        Args:
            text: Очищенный текст вакансии

        Returns:
            List[str]: Список извлеченных элементов
        """
        pass


# ==================== ОБРАБОТКА ОПИСАНИЙ ====================

class IDescriptionProcessor(ABC):
    """
    Интерфейс для комплексной обработки описаний вакансий.

    Определяет контракт для компонентов, координирующих процесс
    извлечения и анализа информации из описаний вакансий.
    """

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
            pd.DataFrame: DataFrame с извлеченными требованиями и обязанностями
        """
        pass

    @abstractmethod
    def get_requirements_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ требований.

        Returns:
            pd.DataFrame: Требования с частотой упоминания
        """
        pass

    @abstractmethod
    def get_responsibilities_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ обязанностей.

        Returns:
            pd.DataFrame: Обязанности с частотой упоминания
        """
        pass

    @abstractmethod
    def get_detailed_vacancy_data(self) -> List[Dict]:
        """
        Получение детальных данных по каждой вакансии.

        Returns:
            List[Dict]: Список словарей с детальной информацией
        """
        pass
