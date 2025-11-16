"""
Модуль анализа данных о вакансиях.

Следует принципу Single Responsibility - отвечает только за анализ данных.
Реализует интерфейс IVacancyAnalyzer (Dependency Inversion).
"""

from typing import List, Dict, Optional
import pandas as pd
from collections import Counter

from core.interfaces import IVacancyAnalyzer


class VacancyAnalyzer(IVacancyAnalyzer):
    """
    Анализатор данных о вакансиях.

    Выполняет различные виды анализа:
    - Извлечение и структурирование данных
    - Анализ навыков и требований
    - Статистика по зарплатам
    - Группировка по компаниям, формату работы и метро

    Attributes:
        vacancies (List[Dict]): Список словарей с данными о вакансиях
        df (Optional[pd.DataFrame]): DataFrame с обработанными данными
    """

    def __init__(self, vacancies: List[Dict]):
        """
        Инициализация анализатора.

        Args:
            vacancies: Список словарей с данными о вакансиях
        """
        self.vacancies = vacancies
        self.df: Optional[pd.DataFrame] = None

    # ==================== ИЗВЛЕЧЕНИЕ ДАННЫХ ====================

    def extract_data(self) -> pd.DataFrame:
        """
        Извлечение и структурирование данных из вакансий.

        Преобразует сырые данные вакансий в структурированный DataFrame
        для дальнейшего анализа.

        Returns:
            pd.DataFrame: Структурированные данные о вакансиях
        """
        data = []

        for vac in self.vacancies:
            # Безопасное извлечение данных с проверкой на None
            salary = vac.get('salary')
            experience = vac.get('experience', {})
            schedule = vac.get('schedule', {})
            employer = vac.get('employer', {})
            address = vac.get('address', {})

            # Обработка информации о метро
            metro_stations = self._extract_metro_stations(address)

            # Формирование записи
            item = {
                'id': vac.get('id'),
                'name': vac.get('name'),
                'company': employer.get('name') if employer else None,
                'company_url': employer.get('alternate_url') if employer else None,
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'currency': salary.get('currency') if salary else None,
                'experience': experience.get('name') if experience else None,
                'schedule': schedule.get('name') if schedule else None,
                'description': vac.get('description', ''),
                'key_skills': [skill['name'] for skill in vac.get('key_skills', [])],
                'url': vac.get('alternate_url'),
                'area': vac.get('area', {}).get('name') if vac.get('area') else None,
                'metro_stations': metro_stations,
                'employment': vac.get('employment', {}).get('name') if vac.get('employment') else None,
            }
            data.append(item)

        self.df = pd.DataFrame(data)
        return self.df

    def _extract_metro_stations(self, address: Optional[Dict]) -> List[str]:
        """
        Извлечение названий станций метро из адреса.

        Args:
            address: Словарь с информацией об адресе

        Returns:
            List[str]: Список названий станций метро
        """
        metro_stations = []

        if not address or not address.get('metro'):
            return metro_stations

        metro = address.get('metro', {})

        # Обработка различных форматов данных метро
        if isinstance(metro, dict):
            station_name = metro.get('station_name', '')
            if station_name:
                metro_stations.append(station_name)
        elif isinstance(metro, list):
            metro_stations = [
                m.get('station_name', '')
                for m in metro
                if m.get('station_name')
            ]

        return metro_stations

    # ==================== АНАЛИЗ НАВЫКОВ ====================

    def analyze_skills(self) -> pd.DataFrame:
        """
        Анализ ключевых навыков из вакансий.

        Подсчитывает частоту упоминания каждого навыка и вычисляет процент.

        Returns:
            pd.DataFrame: Навыки, отсортированные по частоте упоминания
        """
        if self.df is None:
            self.extract_data()

        # Сбор всех навыков
        all_skills = []
        for skills in self.df['key_skills']:
            all_skills.extend(skills)

        # Подсчет частоты
        skills_count = Counter(all_skills)
        skills_df = pd.DataFrame(
            skills_count.most_common(),
            columns=['Навык', 'Количество']
        )

        # Добавление процента
        if len(skills_df) > 0:
            skills_df['Процент'] = (
                    skills_df['Количество'] / len(self.df) * 100
            ).round(2)

        return skills_df

    # ==================== АНАЛИЗ ТРЕБОВАНИЙ ====================

    def analyze_requirements(
            self,
            tech_keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Анализ требований из описаний вакансий.

        Ищет упоминания технических ключевых слов в описаниях вакансий.

        Args:
            tech_keywords: Список ключевых слов для поиска.
                          Если None, используется список по умолчанию.

        Returns:
            pd.DataFrame: Требования, отсортированные по частоте упоминания
        """
        if self.df is None:
            self.extract_data()

        if tech_keywords is None:
            tech_keywords = self._get_default_keywords()

        # Подсчет упоминаний ключевых слов
        requirements_counter = Counter()

        for desc in self.df['description']:
            found_keywords = self._extract_keywords_from_text(
                desc,
                tech_keywords
            )
            requirements_counter.update(found_keywords)

        # Формирование DataFrame
        req_df = pd.DataFrame(
            requirements_counter.most_common(),
            columns=['Требование', 'Количество']
        )

        # Добавление процента
        if len(req_df) > 0:
            req_df['Процент'] = (
                    req_df['Количество'] / len(self.df) * 100
            ).round(2)

        return req_df

    def _extract_keywords_from_text(
            self,
            text: str,
            keywords_list: List[str]
    ) -> List[str]:
        """
        Извлечение ключевых слов из текста.

        Args:
            text: Текст для анализа
            keywords_list: Список ключевых слов для поиска

        Returns:
            List[str]: Найденные ключевые слова
        """
        if not text:
            return []

        text_lower = text.lower()
        found_keywords = []

        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _get_default_keywords(self) -> List[str]:
        """
        Получение списка ключевых слов по умолчанию.

        Returns:
            List[str]: Список технических ключевых слов
        """
        return [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
            'C++', 'C#',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Azure',
            'REST API', 'GraphQL', 'Microservices', 'Git',
            'React', 'Vue', 'Angular', 'Node.js',
            'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
            'English', 'Английский язык', 'Английский'
        ]

    # ==================== СТАТИСТИКА ПО ЗАРПЛАТАМ ====================

    def get_salary_stats(self) -> Dict:
        """
        Вычисление статистики по зарплатам.

        Returns:
            Dict: Словарь со статистическими показателями:
                - count: количество вакансий с указанной зарплатой
                - avg_from/avg_to: средние значения
                - median_from/median_to: медианы
                - min/max: минимум и максимум
        """
        if self.df is None:
            self.extract_data()

        # Фильтрация вакансий с указанной зарплатой
        df_salary = self.df[self.df['salary_from'].notna()].copy()

        if len(df_salary) == 0:
            return {"message": "Нет данных о зарплате"}

        # Вычисление статистик
        stats = {
            'count': len(df_salary),
            'avg_from': df_salary['salary_from'].mean(),
            'avg_to': df_salary['salary_to'].mean(),
            'median_from': df_salary['salary_from'].median(),
            'median_to': df_salary['salary_to'].median(),
            'min': df_salary['salary_from'].min(),
            'max': df_salary['salary_to'].max()
        }

        return stats

    # ==================== ГРУППИРОВКА ПО КОМПАНИЯМ ====================

    def analyze_by_company(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по компаниям.

        Args:
            top_n: Количество топовых компаний для вывода

        Returns:
            pd.DataFrame: Компании с количеством вакансий и процентом
        """
        if self.df is None:
            self.extract_data()

        # Подсчет вакансий по компаниям
        company_counts = self.df['company'].value_counts().reset_index()
        company_counts.columns = ['Компания', 'Количество вакансий']

        # Вычисление процента
        total_vacancies = len(self.df)
        company_counts['Процент'] = (
                company_counts['Количество вакансий'] / total_vacancies * 100
        ).round(2)

        return company_counts.head(top_n)

    # ==================== ГРУППИРОВКА ПО ФОРМАТУ РАБОТЫ ====================

    def analyze_by_schedule(self) -> pd.DataFrame:
        """
        Группировка вакансий по формату работы (schedule).

        Returns:
            pd.DataFrame: Форматы работы с количеством и процентом
        """
        if self.df is None:
            self.extract_data()

        # Подсчет по формату работы
        schedule_counts = self.df['schedule'].fillna('Не указано').value_counts().reset_index()
        schedule_counts.columns = ['Формат работы', 'Количество']

        # Вычисление процента
        total = len(self.df)
        schedule_counts['Процент'] = (
                schedule_counts['Количество'] / total * 100
        ).round(2)

        # Маппинг кодов на читаемые названия
        schedule_mapping = {
            'fullDay': 'Полный день',
            'remote': 'Удаленная работа',
            'flexible': 'Гибкий график',
            'shift': 'Сменный график',
            'flyInFlyOut': 'Вахтовый метод',
        }
        schedule_counts['Формат работы'] = schedule_counts['Формат работы'].replace(
            schedule_mapping
        )

        return schedule_counts

    # ==================== ГРУППИРОВКА ПО МЕТРО ====================

    def analyze_by_metro(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по станциям метро.

        Args:
            top_n: Количество топовых станций для вывода

        Returns:
            pd.DataFrame: Станции метро с количеством вакансий и процентом
        """
        if self.df is None:
            self.extract_data()

        # Сбор всех станций метро
        all_metro_stations = []
        for stations in self.df['metro_stations']:
            if stations:
                all_metro_stations.extend(stations)

        # Проверка наличия данных
        if not all_metro_stations:
            return pd.DataFrame({
                'Станция метро': ['Нет данных'],
                'Количество': [0],
                'Процент': [0.0]
            })

        # Подсчет частоты
        metro_counts = Counter(all_metro_stations)
        metro_df = pd.DataFrame(
            metro_counts.most_common(top_n),
            columns=['Станция метро', 'Количество']
        )

        # Вычисление процента от вакансий с указанным метро
        vacancies_with_metro = sum(
            1 for stations in self.df['metro_stations'] if stations
        )

        if vacancies_with_metro > 0:
            metro_df['Процент'] = (
                    metro_df['Количество'] / vacancies_with_metro * 100
            ).round(2)

        return metro_df
