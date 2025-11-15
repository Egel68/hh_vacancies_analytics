"""
Модуль обработки и анализа данных о вакансиях.

Предоставляет класс VacancyAnalyzer для извлечения,
преобразования и анализа информации о вакансиях.
"""

from typing import List, Dict, Optional
import pandas as pd
from collections import Counter


class VacancyAnalyzer:
    """
    Анализатор данных о вакансиях.

    Attributes:
        vacancies: Список словарей с данными о вакансиях
        df: DataFrame с обработанными данными
    """

    def __init__(self, vacancies: List[Dict]):
        """
        Инициализирует анализатор.

        Args:
            vacancies: Список словарей с данными о вакансиях
        """
        self.vacancies = vacancies
        self.df = None

    def extract_data(self) -> pd.DataFrame:
        """
        Извлекает и структурирует данные из вакансий.

        Returns:
            DataFrame с обработанными данными о вакансиях, содержащий:
                - id: идентификатор вакансии
                - name: название вакансии
                - company: название компании
                - salary_from: нижняя граница зарплаты
                - salary_to: верхняя граница зарплаты
                - currency: валюта зарплаты
                - experience: требуемый опыт
                - schedule: график работы
                - description: описание вакансии
                - key_skills: список ключевых навыков
                - url: ссылка на вакансию
        """
        data = []

        for vac in self.vacancies:
            salary = vac.get('salary')
            experience = vac.get('experience', {})
            schedule = vac.get('schedule', {})
            employer = vac.get('employer', {})

            item = {
                'id': vac.get('id'),
                'name': vac.get('name'),
                'company': employer.get('name'),
                'salary_from': salary.get('from') if salary else None,
                'salary_to': salary.get('to') if salary else None,
                'currency': salary.get('currency') if salary else None,
                'experience': experience.get('name'),
                'schedule': schedule.get('name'),
                'description': vac.get('description', ''),
                'key_skills': [skill['name'] for skill in vac.get('key_skills', [])],
                'url': vac.get('alternate_url')
            }
            data.append(item)

        self.df = pd.DataFrame(data)
        return self.df

    def extract_keywords_from_text(
            self,
            text: str,
            keywords_list: List[str]
    ) -> List[str]:
        """
        Извлекает ключевые слова из текста.

        Args:
            text: Текст для анализа
            keywords_list: Список ключевых слов для поиска

        Returns:
            Список найденных ключевых слов
        """
        text_lower = text.lower()
        found_keywords = []

        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def analyze_skills(self) -> pd.DataFrame:
        """
        Анализирует ключевые навыки из вакансий.

        Returns:
            DataFrame со статистикой по навыкам, содержащий:
                - Навык: название навыка
                - Количество: количество упоминаний
                - Процент: процент вакансий с этим навыком
        """
        all_skills = []

        for skills in self.df['key_skills']:
            all_skills.extend(skills)

        skills_count = Counter(all_skills)
        skills_df = pd.DataFrame(
            skills_count.most_common(),
            columns=['Навык', 'Количество']
        )

        if len(skills_df) > 0:
            skills_df['Процент'] = (skills_df['Количество'] / len(self.df) * 100).round(2)

        return skills_df

    def analyze_requirements(
            self,
            tech_keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Анализирует требования из описаний вакансий.

        Args:
            tech_keywords: Список технологий и требований для поиска.
                          Если None, используется стандартный набор

        Returns:
            DataFrame со статистикой по требованиям, содержащий:
                - Требование: название требования/технологии
                - Количество: количество упоминаний
                - Процент: процент вакансий с этим требованием
        """
        if tech_keywords is None:
            tech_keywords = [
                # Языки программирования
                'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
                'C++', 'C#', 'SQL',
                # Python фреймворки
                'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp',
                # Базы данных
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
                'ClickHouse',
                # DevOps
                'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI',
                # Облака
                'AWS', 'Azure', 'Google Cloud', 'GCP',
                # API
                'REST API', 'GraphQL', 'Microservices',
                # Методологии
                'Agile', 'Scrum', 'Git',
                # ML/DS
                'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
                # Frontend
                'React', 'Vue', 'Angular', 'Node.js',
                # Языки
                'English', 'Английский язык', 'Английский'
            ]

        requirements_counter = Counter()

        for desc in self.df['description']:
            found_keywords = self.extract_keywords_from_text(desc, tech_keywords)
            requirements_counter.update(found_keywords)

        req_df = pd.DataFrame(
            requirements_counter.most_common(),
            columns=['Требование', 'Количество']
        )

        if len(req_df) > 0:
            req_df['Процент'] = (req_df['Количество'] / len(self.df) * 100).round(2)

        return req_df

    def get_salary_stats(self) -> Dict:
        """
        Вычисляет статистику по зарплатам.

        Returns:
            Словарь со статистикой, содержащий:
                - count: количество вакансий с указанной зарплатой
                - avg_from: средняя нижняя граница зарплаты
                - avg_to: средняя верхняя граница зарплаты
                - median_from: медианная нижняя граница зарплаты
                - median_to: медианная верхняя граница зарплаты
                - min: минимальная зарплата
                - max: максимальная зарплата
            Или сообщение об отсутствии данных
        """
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
