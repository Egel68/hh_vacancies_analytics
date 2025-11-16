"""
Модуль оркестрации процесса анализа вакансий.
Объединяет все компоненты системы (Facade pattern).
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

from core.interfaces import (
    IVacancySearcher,
    IVacancyDetailsFetcher,
    IVacancyAnalyzer,
    IVacancyVisualizer
)
from storage.savers import JsonSaver, CsvSaver


class VacancyPipeline:
    """
    Главный класс для управления процессом анализа вакансий.

    Реализует паттерн Facade для упрощения работы с системой.
    Следует принципу Open/Closed - открыт для расширения через DI.
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
            max_vacancies: int = 100,
            show_plots: bool = False,
            tech_keywords: Optional[List[str]] = None
    ) -> Dict:
        """
        Обработка одного запроса.

        Args:
            query: Название должности
            area: Код региона
            max_vacancies: Максимальное количество вакансий
            show_plots: Показывать ли графики
            tech_keywords: Ключевые слова для анализа требований

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
        vacancies_list = self.searcher.search(query, area, max_pages=10)

        if not vacancies_list:
            print(f"❌ Вакансии не найдены для: {query}")
            return {}

        # Ограничение количества
        vacancies_list = vacancies_list[:max_vacancies]

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

        # 7. Анализ требований
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

        # 9. Визуализация
        self.visualizer.visualize(analyzer, str(output_dir), show_plots)

        # 10. Формирование сводки
        top_skills = (
            skills_df.head(5)['Навык'].tolist()
            if len(skills_df) > 0 else []
        )

        summary = {
            'Должность': query,
            'Вакансий': len(df),
            'Топ-5 навыков': ', '.join(top_skills),
            'Средняя ЗП (от)': salary_stats.get('avg_from', 'N/A'),
            'Медиана ЗП (от)': salary_stats.get('median_from', 'N/A'),
            'Папка': str(output_dir)
        }

        print(f"\n✅ Анализ завершен для: {query}")
        print(f"📁 Результаты в папке: {output_dir}")

        return summary

    def process_batch_queries(
            self,
            queries: List[str],
            area: int = 1,
            max_vacancies: int = 100,
            show_plots: bool = False,
            tech_keywords: Optional[List[str]] = None
    ) -> None:
        """
        Пакетная обработка нескольких запросов.

        Args:
            queries: Список названий должностей
            area: Код региона
            max_vacancies: Максимальное количество вакансий
            show_plots: Показывать ли графики
            tech_keywords: Ключевые слова для анализа
        """
        print("=" * 60)
        print("🔄 ПАКЕТНЫЙ АНАЛИЗ ВАКАНСИЙ")
        print("=" * 60)
        print(f"Должности: {', '.join(queries)}\n")

        summary_list = []

        # Обработка каждого запроса
        for query in queries:
            summary = self.process_single_query(
                query=query,
                area=area,
                max_vacancies=max_vacancies,
                show_plots=show_plots,
                tech_keywords=tech_keywords
            )

            if summary:
                summary_list.append(summary)

        # Создание общей сводки
        if summary_list:
            summary_df = pd.DataFrame(summary_list)
            summary_path = self.output_dir / 'batch_summary.csv'
            self.csv_saver.save(summary_df, str(summary_path))

            print("\n" + "=" * 60)
            print("📋 ОБЩАЯ СВОДКА")
            print("=" * 60)
            print(summary_df.to_string(index=False))

        print("\n✅ Пакетный анализ завершен!")
