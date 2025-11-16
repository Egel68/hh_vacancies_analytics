"""
Модуль координации процесса обработки описаний вакансий.
Объединяет очистку текста и извлечение информации (Facade pattern).
Следует принципам Single Responsibility и Dependency Inversion.
"""

from typing import List, Dict
from collections import Counter
import pandas as pd

from core.interfaces import (
    ITextCleaner,
    ITextSectionExtractor,
    IDescriptionProcessor
)
from extractors.item_classifier import VacancyItemClassifier


class VacancyDescriptionProcessor(IDescriptionProcessor):
    """
    Процессор для комплексной обработки описаний вакансий.

    Координирует работу компонентов очистки и извлечения данных.
    Следует принципу Dependency Inversion - зависит от абстракций, а не от конкретных реализаций.
    Следует принципу Single Responsibility - отвечает только за координацию процесса.
    Реализует паттерн Facade - предоставляет простой интерфейс к сложной системе.
    """

    def __init__(
            self,
            text_cleaner: ITextCleaner,
            requirements_extractor: ITextSectionExtractor,
            responsibilities_extractor: ITextSectionExtractor,
            use_classifier: bool = True  # НОВЫЙ ПАРАМЕТР
    ):
        """
        Инициализация процессора.

        Args:
            text_cleaner: Компонент очистки текста от HTML
            requirements_extractor: Экстрактор требований
            responsibilities_extractor: Экстрактор обязанностей
            use_classifier: Использовать ли классификатор для разделения
        """
        self.text_cleaner = text_cleaner
        self.requirements_extractor = requirements_extractor
        self.responsibilities_extractor = responsibilities_extractor
        self.use_classifier = use_classifier

        # Классификатор для разделения смешанных данных
        self.classifier = VacancyItemClassifier() if use_classifier else None

        # Хранение результатов обработки
        self.processed_data: List[Dict] = []
        self.all_requirements: List[str] = []
        self.all_responsibilities: List[str] = []

    def process_vacancies(self, vacancies: List[Dict]) -> pd.DataFrame:
        """
        Обработка описаний всех вакансий.

        Args:
            vacancies: Список вакансий с полем description

        Returns:
            DataFrame с извлеченными требованиями и обязанностями
        """
        print(f"\n🔍 Обработка описаний {len(vacancies)} вакансий...")

        # Сброс данных
        self.processed_data = []
        self.all_requirements = []
        self.all_responsibilities = []

        # Обработка каждой вакансии
        for idx, vacancy in enumerate(vacancies, 1):
            if idx % 50 == 0 or idx == len(vacancies):
                print(f"   Обработано: {idx}/{len(vacancies)}")

            result = self._process_single_vacancy(vacancy)

            if result:
                self.processed_data.append(result)
                self.all_requirements.extend(result['requirements'])
                self.all_responsibilities.extend(result['responsibilities'])

        print(f"✅ Обработка завершена")
        print(f"   Извлечено уникальных требований: {len(set(self.all_requirements))}")
        print(f"   Извлечено уникальных обязанностей: {len(set(self.all_responsibilities))}")

        return self._create_dataframe()

    def _process_single_vacancy(self, vacancy: Dict) -> Dict:
        """
        Обработка одной вакансии.

        Args:
            vacancy: Словарь с данными вакансии

        Returns:
            Словарь с результатами обработки или None
        """
        raw_description = vacancy.get('description', '')

        if not raw_description:
            return None

        # Шаг 1: Очистка текста от HTML
        clean_text = self.text_cleaner.clean(raw_description)

        if not clean_text or len(clean_text) < 50:
            return None

        # Шаг 2: Извлечение требований
        requirements = self.requirements_extractor.extract(clean_text)

        # Шаг 3: Извлечение обязанностей
        responsibilities = self.responsibilities_extractor.extract(clean_text)

        # ========== НОВАЯ ЛОГИКА: КЛАССИФИКАЦИЯ СМЕШАННЫХ ДАННЫХ ==========

        if self.use_classifier and self.classifier:
            # Разделение требований (могут содержать обязанности)
            req_filtered, req_misclassified = self.classifier.separate_mixed_items(
                requirements
            )

            # Разделение обязанностей (могут содержать требования)
            resp_misclassified, resp_filtered = self.classifier.separate_mixed_items(
                responsibilities
            )

            # Объединение с учетом переклассификации
            final_requirements = list(set(req_filtered + resp_misclassified))
            final_responsibilities = list(set(resp_filtered + req_misclassified))
        else:
            final_requirements = requirements
            final_responsibilities = responsibilities

        # ===================================================================

        return {
            'vacancy_id': vacancy.get('id'),
            'vacancy_name': vacancy.get('name'),
            'company': vacancy.get('employer', {}).get('name') if vacancy.get('employer') else None,
            'clean_description': clean_text,
            'requirements': final_requirements,
            'responsibilities': final_responsibilities,
            'requirements_count': len(final_requirements),
            'responsibilities_count': len(final_responsibilities),
        }

    def _create_dataframe(self) -> pd.DataFrame:
        """
        Создание DataFrame из обработанных данных.

        Returns:
            DataFrame с результатами
        """
        if not self.processed_data:
            return pd.DataFrame()

        # Преобразование для DataFrame (склеивание списков в строки)
        df_data = []

        for item in self.processed_data:
            df_data.append({
                'vacancy_id': item['vacancy_id'],
                'vacancy_name': item['vacancy_name'],
                'company': item['company'],
                'requirements': '; '.join(item['requirements']) if item['requirements'] else '',
                'responsibilities': '; '.join(item['responsibilities']) if item['responsibilities'] else '',
                'requirements_count': item['requirements_count'],
                'responsibilities_count': item['responsibilities_count'],
            })

        return pd.DataFrame(df_data)

    def get_requirements_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ требований.

        Returns:
            DataFrame с частотой встречаемости требований
        """
        if not self.all_requirements:
            return pd.DataFrame(columns=['Требование', 'Частота', 'Процент'])

        # Подсчет частоты встречаемости
        counter = Counter(self.all_requirements)
        total_vacancies = len(self.processed_data)

        freq_data = []
        for requirement, count in counter.most_common(100):  # Увеличено до 100
            freq_data.append({
                'Требование': requirement,
                'Частота': count,
                'Процент': round(count / total_vacancies * 100, 2)
            })

        return pd.DataFrame(freq_data)

    def get_responsibilities_frequency(self) -> pd.DataFrame:
        """
        Частотный анализ обязанностей.

        Returns:
            DataFrame с частотой встречаемости обязанностей
        """
        if not self.all_responsibilities:
            return pd.DataFrame(columns=['Обязанность', 'Частота', 'Процент'])

        # Подсчет частоты встречаемости
        counter = Counter(self.all_responsibilities)
        total_vacancies = len(self.processed_data)

        freq_data = []
        for responsibility, count in counter.most_common(100):  # Увеличено до 100
            freq_data.append({
                'Обязанность': responsibility,
                'Частота': count,
                'Процент': round(count / total_vacancies * 100, 2)
            })

        return pd.DataFrame(freq_data)

    def get_detailed_vacancy_data(self) -> List[Dict]:
        """
        Получение детальных данных по каждой вакансии.

        Returns:
            Список словарей с детальной информацией
        """
        return self.processed_data

    def get_statistics(self) -> Dict:
        """
        Получение общей статистики по обработке.

        Returns:
            Словарь со статистикой
        """
        if not self.processed_data:
            return {}

        total_requirements = len(self.all_requirements)
        total_responsibilities = len(self.all_responsibilities)
        unique_requirements = len(set(self.all_requirements))
        unique_responsibilities = len(set(self.all_responsibilities))

        avg_req_per_vacancy = total_requirements / len(self.processed_data) if self.processed_data else 0
        avg_resp_per_vacancy = total_responsibilities / len(self.processed_data) if self.processed_data else 0

        return {
            'total_vacancies_processed': len(self.processed_data),
            'total_requirements_extracted': total_requirements,
            'total_responsibilities_extracted': total_responsibilities,
            'unique_requirements': unique_requirements,
            'unique_responsibilities': unique_responsibilities,
            'avg_requirements_per_vacancy': round(avg_req_per_vacancy, 2),
            'avg_responsibilities_per_vacancy': round(avg_resp_per_vacancy, 2),
            'classifier_used': self.use_classifier
        }
