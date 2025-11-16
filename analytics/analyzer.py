"""
Модуль анализа данных о вакансиях.
Следует принципу Single Responsibility - только анализ данных.
"""

from typing import List, Dict, Optional
import pandas as pd
from collections import Counter
from core.interfaces import IVacancyAnalyzer


class VacancyAnalyzer(IVacancyAnalyzer):
    """
    Анализатор данных о вакансиях.

    Attributes:
        vacancies: Список словарей с данными о вакансиях
        df: DataFrame с обработанными данными
    """

    def __init__(self, vacancies: List[Dict]):
        """
        Инициализация анализатора.

        Args:
            vacancies: Список словарей с данными о вакансиях
        """
        self.vacancies = vacancies
        self.df = None

    def extract_data(self) -> pd.DataFrame:
        """Извлечение и структурирование данных из вакансий."""
        data = []

        for vac in self.vacancies:
            salary = vac.get('salary')
            experience = vac.get('experience', {})
            schedule = vac.get('schedule', {})
            employer = vac.get('employer', {})
            address = vac.get('address', {})

            # Извлечение станций метро
            metro_stations = []
            if address and address.get('metro'):
                metro = address.get('metro', {})
                if isinstance(metro, dict):
                    metro_stations.append(metro.get('station_name', ''))
                elif isinstance(metro, list):
                    metro_stations = [m.get('station_name', '') for m in metro if m.get('station_name')]

            item = {
                'id': vac.get('id'),
                'name': vac.get('name'),
                'company': employer.get('name'),
                'company_url': employer.get('alternate_url'),
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'currency': salary.get('currency') if salary else None,
                'experience': experience.get('name'),
                'schedule': schedule.get('name'),
                'description': vac.get('description', ''),
                'key_skills': [skill['name'] for skill in vac.get('key_skills', [])],
                'url': vac.get('alternate_url'),
                'area': vac.get('area', {}).get('name'),
                'metro_stations': metro_stations,
                'employment': vac.get('employment', {}).get('name'),
            }
            data.append(item)

        self.df = pd.DataFrame(data)
        return self.df

    def analyze_skills(self) -> pd.DataFrame:
        """Анализ ключевых навыков из вакансий."""
        if self.df is None:
            self.extract_data()

        all_skills = []
        for skills in self.df['key_skills']:
            all_skills.extend(skills)

        skills_count = Counter(all_skills)
        skills_df = pd.DataFrame(
            skills_count.most_common(),
            columns=['Навык', 'Количество']
        )

        if len(skills_df) > 0:
            skills_df['Процент'] = (
                    skills_df['Количество'] / len(self.df) * 100
            ).round(2)

        return skills_df

    def analyze_requirements(
            self,
            tech_keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Анализ требований из описаний вакансий."""
        if self.df is None:
            self.extract_data()

        if tech_keywords is None:
            tech_keywords = self._get_default_keywords()

        requirements_counter = Counter()

        for desc in self.df['description']:
            found_keywords = self._extract_keywords_from_text(
                desc,
                tech_keywords
            )
            requirements_counter.update(found_keywords)

        req_df = pd.DataFrame(
            requirements_counter.most_common(),
            columns=['Требование', 'Количество']
        )

        if len(req_df) > 0:
            req_df['Процент'] = (
                    req_df['Количество'] / len(self.df) * 100
            ).round(2)

        return req_df

    def get_salary_stats(self) -> Dict:
        """Вычисление статистики по зарплатам."""
        if self.df is None:
            self.extract_data()

        df_salary = self.df[self.df['salary_from'].notna()].copy()

        if len(df_salary) == 0:
            return {"message": "Нет данных о зарплате"}

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

    # ========== НОВЫЕ МЕТОДЫ ГРУППИРОВКИ ==========

    def analyze_by_company(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по компаниям.

        Args:
            top_n: Количество топовых компаний

        Returns:
            DataFrame с компаниями и количеством вакансий
        """
        if self.df is None:
            self.extract_data()

        # Подсчет вакансий по компаниям
        company_counts = self.df['company'].value_counts().reset_index()
        company_counts.columns = ['Компания', 'Количество вакансий']

        # Добавление процента
        total_vacancies = len(self.df)
        company_counts['Процент'] = (
                company_counts['Количество вакансий'] / total_vacancies * 100
        ).round(2)

        # Ограничение топ-N
        return company_counts.head(top_n)

    def analyze_by_schedule(self) -> pd.DataFrame:
        """
        Группировка вакансий по формату работы.

        Returns:
            DataFrame с форматами работы и их количеством
        """
        if self.df is None:
            self.extract_data()

        # Подсчет по графику работы
        schedule_counts = self.df['schedule'].fillna('Не указано').value_counts().reset_index()
        schedule_counts.columns = ['Формат работы', 'Количество']

        # Добавление процента
        total = len(self.df)
        schedule_counts['Процент'] = (
                schedule_counts['Количество'] / total * 100
        ).round(2)

        # Переименование для читаемости
        schedule_mapping = {
            'fullDay': 'Полный день',
            'remote': 'Удаленная работа',
            'flexible': 'Гибкий график',
            'shift': 'Сменный график',
            'flyInFlyOut': 'Вахтовый метод',
        }

        schedule_counts['Формат работы'] = schedule_counts['Формат работы'].replace(schedule_mapping)

        return schedule_counts

    def analyze_by_metro(self, top_n: int = 20) -> pd.DataFrame:
        """
        Группировка вакансий по станциям метро.

        Args:
            top_n: Количество топовых станций

        Returns:
            DataFrame со станциями метро и количеством вакансий
        """
        if self.df is None:
            self.extract_data()

        # Собираем все станции метро
        all_metro_stations = []
        for stations in self.df['metro_stations']:
            if stations:
                all_metro_stations.extend(stations)

        if not all_metro_stations:
            return pd.DataFrame({
                'Станция метро': ['Нет данных'],
                'Количество': [0],
                'Процент': [0.0]
            })

        # Подсчет
        metro_counts = Counter(all_metro_stations)
        metro_df = pd.DataFrame(
            metro_counts.most_common(top_n),
            columns=['Станция метро', 'Количество']
        )

        # Процент от вакансий с указанным метро
        vacancies_with_metro = sum(1 for stations in self.df['metro_stations'] if stations)

        if vacancies_with_metro > 0:
            metro_df['Процент'] = (
                    metro_df['Количество'] / vacancies_with_metro * 100
            ).round(2)

        return metro_df

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def _extract_keywords_from_text(
            self,
            text: str,
            keywords_list: List[str]
    ) -> List[str]:
        """Извлечение ключевых слов из текста."""
        if not text:
            return []

        text_lower = text.lower()
        found_keywords = []

        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _get_default_keywords(self) -> List[str]:
        """Получение списка ключевых слов по умолчанию."""
        return [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
            'C++', 'C#', 'SQL', 'Django', 'Flask', 'FastAPI',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Azure',
            'REST API', 'GraphQL', 'Microservices', 'Git',
            'React', 'Vue', 'Angular', 'Node.js',
            'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
            'English', 'Английский язык', 'Английский'
        ]
