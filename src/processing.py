from typing import List, Dict
import pandas as pd
from collections import Counter


class VacancyAnalyzer:
    def __init__(self, vacancies: List[Dict]):
        self.vacancies = vacancies
        self.df = None

    def extract_data(self) -> pd.DataFrame:
        """Извлечение нужных данных из вакансий"""
        data = []

        for vac in self.vacancies:
            item = {
                'id': vac.get('id'),
                'name': vac.get('name'),
                'company': vac.get('employer', {}).get('name'),
                'salary_from': vac.get('salary', {}).get('from') if vac.get('salary') else None,
                'salary_to': vac.get('salary', {}).get('to') if vac.get('salary') else None,
                'currency': vac.get('salary', {}).get('currency') if vac.get('salary') else None,
                'experience': vac.get('experience', {}).get('name'),
                'schedule': vac.get('schedule', {}).get('name'),
                'description': vac.get('description', ''),
                'key_skills': [skill['name'] for skill in vac.get('key_skills', [])],
                'url': vac.get('alternate_url')
            }
            data.append(item)

        self.df = pd.DataFrame(data)
        return self.df

    def extract_keywords_from_text(self, text: str, keywords_list: List[str]) -> List[str]:
        """Извлечение ключевых слов из текста"""
        text_lower = text.lower()
        found_keywords = []

        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def analyze_skills(self) -> pd.DataFrame:
        """Анализ навыков"""
        all_skills = []

        for skills in self.df['key_skills']:
            all_skills.extend(skills)

        skills_count = Counter(all_skills)
        skills_df = pd.DataFrame(skills_count.most_common(),
                                 columns=['Навык', 'Количество'])

        if len(skills_df) > 0:
            skills_df['Процент'] = (skills_df['Количество'] / len(self.df) * 100).round(2)

        return skills_df

    def analyze_requirements(self, tech_keywords: List[str] = None) -> pd.DataFrame:
        """Анализ требований из описания вакансий"""
        if tech_keywords is None:
            # Расширенный список технологий и требований
            tech_keywords = [
                # Языки программирования
                'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang', 'C++', 'C#', 'SQL',

                # Python фреймворки
                'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp',

                # Базы данных
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'ClickHouse',

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

        req_df = pd.DataFrame(requirements_counter.most_common(),
                              columns=['Требование', 'Количество'])

        if len(req_df) > 0:
            req_df['Процент'] = (req_df['Количество'] / len(self.df) * 100).round(2)

        return req_df

    def get_salary_stats(self) -> Dict:
        """Статистика по зарплатам"""
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
