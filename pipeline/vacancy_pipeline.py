"""
Модуль оркестрации процесса анализа вакансий.
Объединяет все компоненты системы (Facade pattern).
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

from config import Config  # ← ПЕРЕНЕСЕН В НАЧАЛО
from core.interfaces import (
    IVacancySearcher,
    IVacancyDetailsFetcher,
    IVacancyAnalyzer,
    IVacancyVisualizer,
    IDescriptionProcessor
)
from storage.savers import JsonSaver, CsvSaver
from parsers.text_cleaner import HtmlTextCleaner
from extractors.requirements_extractor import (
    RequirementsExtractor,
    SkillsBasedRequirementsExtractor
)
from extractors.responsibilities_extractor import ResponsibilitiesExtractor
from processors.description_processor import VacancyDescriptionProcessor


class VacancyPipeline:
    """
    Главный класс для управления процессом анализа вакансий.

    Реализует паттерн Facade для упрощения работы с системой.
    Следует принципу Open/Closed - открыт для расширения через DI.
    Следует принципу Dependency Inversion - зависит от интерфейсов.
    """

    def __init__(
            self,
            searcher: IVacancySearcher,
            details_fetcher: IVacancyDetailsFetcher,
            analyzer_class: type,
            visualizer: IVacancyVisualizer,
            output_dir: str = "./result"
    ):
        """
        Инициализация pipeline.

        Args:
            searcher: Компонент для поиска вакансий
            details_fetcher: Компонент для получения деталей
            analyzer_class: Класс анализатора (будет создан для каждого запроса)
            visualizer: Компонент для визуализации
            output_dir: Базовая директория для результатов
        """
        self.searcher = searcher
        self.details_fetcher = details_fetcher
        self.analyzer_class = analyzer_class
        self.visualizer = visualizer
        self.output_dir = Path(output_dir)

        self.json_saver = JsonSaver()
        self.csv_saver = CsvSaver()

    def process_single_query(
            self,
            query: str,
            area: int = 1,
            max_vacancies: Optional[int] = 1000,
            max_pages: int = 20,
            show_plots: bool = False,
            tech_keywords: Optional[List[str]] = None,
            process_descriptions: bool = True
    ) -> Dict:
        """
        Обработка одного запроса.

        Args:
            query: Название должности
            area: Код региона
            max_vacancies: Максимальное количество вакансий (None = все)
            max_pages: Максимальное количество страниц для парсинга
            show_plots: Показывать ли графики
            tech_keywords: Ключевые слова для анализа требований
            process_descriptions: Обрабатывать ли описания для извлечения требований/задач

        Returns:
            Словарь со статистикой анализа
        """
        safe_query = query.replace(' ', '_').replace('/', '_').lower()
        output_dir = self.output_dir / safe_query
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'=' * 60}")
        print(f"📊 Анализ: {query}")
        print(f"{'=' * 60}")

        # 1. Поиск вакансий
        vacancies_list = self.searcher.search(
            query,
            area,
            max_pages=max_pages,
            max_vacancies=max_vacancies
        )

        if not vacancies_list:
            print(f"❌ Вакансии не найдены для: {query}")
            return {}

        # 2. Получение детальной информации
        detailed_vacancies = self.details_fetcher.fetch_details(vacancies_list)

        if not detailed_vacancies:
            print(f"❌ Не удалось получить детали для: {query}")
            return {}

        # 3. Сохранение сырых данных
        self.json_saver.save(
            detailed_vacancies,
            str(output_dir / 'raw.json')
        )

        # 4. Анализ данных
        print(f"\n📊 Анализ данных...")
        analyzer = self.analyzer_class(detailed_vacancies)
        df = analyzer.extract_data()

        # 5. Сохранение обработанных данных
        self.csv_saver.save(df, str(output_dir / 'processed.csv'))

        # 6. Анализ навыков
        skills_df = analyzer.analyze_skills()
        if len(skills_df) > 0:
            self.csv_saver.save(skills_df, str(output_dir / 'skills.csv'))

        # 7. Анализ требований (из key_skills)
        requirements_df = analyzer.analyze_requirements(tech_keywords)
        if len(requirements_df) > 0:
            self.csv_saver.save(
                requirements_df,
                str(output_dir / 'requirements.csv')
            )

        # 8. Статистика по зарплатам
        salary_stats = analyzer.get_salary_stats()
        self.json_saver.save(
            salary_stats,
            str(output_dir / 'salary_stats.json')
        )

        # 9. Анализ по компаниям
        companies_df = analyzer.analyze_by_company(top_n=20)
        if len(companies_df) > 0:
            self.csv_saver.save(companies_df, str(output_dir / 'companies.csv'))

        # 10. Анализ по формату работы
        schedule_df = analyzer.analyze_by_schedule()
        if len(schedule_df) > 0:
            self.csv_saver.save(schedule_df, str(output_dir / 'schedule.csv'))

        # 11. Анализ по станциям метро
        metro_df = analyzer.analyze_by_metro(top_n=20)
        if len(metro_df) > 0 and metro_df.iloc[0]['Станция метро'] != 'Нет данных':
            self.csv_saver.save(metro_df, str(output_dir / 'metro.csv'))

        # ========== ОБРАБОТКА ОПИСАНИЙ ==========

        description_processor = None

        if process_descriptions:
            description_processor = self._process_vacancy_descriptions(
                detailed_vacancies,
                output_dir,
                tech_keywords
            )

        # =========================================

        # 12. Визуализация
        self.visualizer.visualize(analyzer, str(output_dir), show_plots)

        # 13. Формирование сводки
        top_skills = (
            skills_df.head(5)['Навык'].tolist()
            if len(skills_df) > 0 else []
        )

        top_companies = (
            companies_df.head(3)['Компания'].tolist()
            if len(companies_df) > 0 else []
        )

        summary = {
            'Должность': query,
            'Вакансий собрано': len(df),
            'Топ-5 навыков': ', '.join(top_skills),
            'Топ-3 компании': ', '.join(top_companies),
            'Средняя ЗП (от)': salary_stats.get('avg_from', 'N/A'),
            'Медиана ЗП (от)': salary_stats.get('median_from', 'N/A'),
            'Папка': str(output_dir)
        }

        # Добавление статистики по описаниям
        if description_processor:
            desc_stats = description_processor.get_statistics()
            summary.update({
                'Извлечено требований': desc_stats.get('total_requirements_extracted', 0),
                'Извлечено обязанностей': desc_stats.get('total_responsibilities_extracted', 0),
            })

        print(f"\n✅ Анализ завершен для: {query}")
        print(f"📁 Результаты в папке: {output_dir}")

        return summary

    def _process_vacancy_descriptions(
            self,
            detailed_vacancies: List[Dict],
            output_dir: Path,
            tech_keywords: Optional[List[str]] = None
    ) -> IDescriptionProcessor:
        """
        Обработка описаний вакансий для извлечения требований и обязанностей.

        Args:
            detailed_vacancies: Список детальной информации о вакансиях
            output_dir: Директория для сохранения результатов
            tech_keywords: Ключевые слова для анализа требований

        Returns:
            Процессор описаний вакансий
        """
        print(f"\n📝 Обработка описаний вакансий...")

        # Создание компонентов
        text_cleaner = HtmlTextCleaner(preserve_structure=True)

        # Выбор экстрактора требований
        if tech_keywords:
            requirements_extractor = SkillsBasedRequirementsExtractor(
                tech_keywords=tech_keywords,
                min_length=Config.REQ_MIN_LENGTH,
                max_length=Config.REQ_MAX_LENGTH,
                min_words=Config.REQ_MIN_WORDS,
                similarity_threshold=Config.SIMILARITY_THRESHOLD
            )
        else:
            requirements_extractor = RequirementsExtractor(
                min_length=Config.REQ_MIN_LENGTH,
                max_length=Config.REQ_MAX_LENGTH,
                min_words=Config.REQ_MIN_WORDS,
                similarity_threshold=Config.SIMILARITY_THRESHOLD
            )

        # ========== ИСПРАВЛЕНО: используем параметры из Config ==========
        responsibilities_extractor = ResponsibilitiesExtractor(
            min_length=Config.RESP_MIN_LENGTH,
            max_length=Config.RESP_MAX_LENGTH,
            min_words=Config.RESP_MIN_WORDS,
            similarity_threshold=Config.SIMILARITY_THRESHOLD
        )
        # ================================================================

        # Создание процессора с классификатором
        processor = VacancyDescriptionProcessor(
            text_cleaner=text_cleaner,
            requirements_extractor=requirements_extractor,
            responsibilities_extractor=responsibilities_extractor,
            use_classifier=Config.USE_CLASSIFIER
        )

        # Обработка вакансий
        df = processor.process_vacancies(detailed_vacancies)

        # Сохранение результатов
        if len(df) > 0:
            self.csv_saver.save(
                df,
                str(output_dir / 'extracted_requirements_responsibilities.csv')
            )
            print(f"  ✅ Сохранено: extracted_requirements_responsibilities.csv")

        # Частотный анализ требований
        req_freq = processor.get_requirements_frequency()
        if len(req_freq) > 0:
            self.csv_saver.save(
                req_freq,
                str(output_dir / 'requirements_frequency.csv')
            )
            print(f"  ✅ Сохранено: requirements_frequency.csv")
            print(f"\n📊 Топ-10 наиболее частых требований:")
            for idx, row in req_freq.head(10).iterrows():
                print(f"   {idx + 1}. {row['Требование'][:60]}... ({row['Частота']} - {row['Процент']}%)")

        # Частотный анализ обязанностей
        resp_freq = processor.get_responsibilities_frequency()
        if len(resp_freq) > 0:
            self.csv_saver.save(
                resp_freq,
                str(output_dir / 'responsibilities_frequency.csv')
            )
            print(f"  ✅ Сохранено: responsibilities_frequency.csv")
            print(f"\n📊 Топ-10 наиболее частых обязанностей:")
            for idx, row in resp_freq.head(10).iterrows():
                print(f"   {idx + 1}. {row['Обязанность'][:60]}... ({row['Частота']} - {row['Процент']}%)")

        # Детальные данные в JSON
        detailed_data = processor.get_detailed_vacancy_data()
        self.json_saver.save(
            detailed_data,
            str(output_dir / 'detailed_extracted_data.json')
        )
        print(f"  ✅ Сохранено: detailed_extracted_data.json")

        # Статистика обработки
        stats = processor.get_statistics()
        self.json_saver.save(
            stats,
            str(output_dir / 'description_processing_stats.json')
        )
        print(f"  ✅ Сохранено: description_processing_stats.json")
        print(f"\n📊 Статистика обработки:")
        print(f"   Вакансий обработано: {stats.get('total_vacancies_processed', 0)}")
        print(f"   Классификатор использован: {'ДА' if stats.get('classifier_used') else 'НЕТ'}")
        print(f"   Требований извлечено: {stats.get('total_requirements_extracted', 0)}")
        print(f"   Обязанностей извлечено: {stats.get('total_responsibilities_extracted', 0)}")

        return processor

    def process_batch_queries(
            self,
            queries: List[str],
            area: int = 1,
            max_vacancies: Optional[int] = 1000,
            max_pages: int = 20,
            show_plots: bool = False,
            tech_keywords: Optional[List[str]] = None,
            process_descriptions: bool = True
    ) -> pd.DataFrame:
        """
        Обработка нескольких запросов.

        Args:
            queries: Список названий должностей
            area: Код региона
            max_vacancies: Максимальное количество вакансий (None = все)
            max_pages: Максимальное количество страниц для парсинга
            show_plots: Показывать ли графики
            tech_keywords: Ключевые слова для анализа требований
            process_descriptions: Обрабатывать ли описания для извлечения требований/задач

        Returns:
            DataFrame со сводной статистикой по всем запросам
        """
        print(f"\n{'=' * 60}")
        print(f"🔄 Batch-анализ: {len(queries)} запросов")
        print(f"{'=' * 60}")

        summaries = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Обработка: {query}")

            summary = self.process_single_query(
                query=query,
                area=area,
                max_vacancies=max_vacancies,
                max_pages=max_pages,
                show_plots=show_plots,
                tech_keywords=tech_keywords,
                process_descriptions=process_descriptions
            )

            if summary:
                summaries.append(summary)

        # Создание сводного отчета
        if summaries:
            summary_df = pd.DataFrame(summaries)
            summary_path = self.output_dir / 'batch_summary.csv'
            self.csv_saver.save(summary_df, str(summary_path))

            print(f"\n{'=' * 60}")
            print(f"✅ Batch-анализ завершен")
            print(f"📊 Обработано запросов: {len(summaries)}/{len(queries)}")
            print(f"📁 Сводный отчет: {summary_path}")
            print(f"{'=' * 60}\n")

            return summary_df
        else:
            print(f"\n❌ Не удалось обработать ни один запрос")
            return pd.DataFrame()
