"""
Точка входа в приложение.
Создает и конфигурирует все компоненты согласно принципу Dependency Injection.
"""

from config import Config
from fetchers.searcher import SyncVacancySearcher, AsyncVacancySearcher
from fetchers.details_fetcher import (
    SyncVacancyDetailsFetcher,
    AsyncVacancyDetailsFetcher
)
from analytics.analyzer import VacancyAnalyzer
from visualization.visualizer import VacancyVisualizer
from pipeline.vacancy_pipeline import VacancyPipeline


def create_pipeline(config: Config) -> VacancyPipeline:
    """
    Фабрика для создания pipeline с нужными компонентами.

    Реализует Dependency Injection - все зависимости передаются извне.

    Args:
        config: Объект конфигурации

    Returns:
        Настроенный VacancyPipeline
    """
    # Выбор компонентов на основе конфигурации
    if config.PARSING_MODE == 'async':
        searcher = AsyncVacancySearcher(max_concurrent=config.MAX_CONCURRENT)
        details_fetcher = AsyncVacancyDetailsFetcher(
            max_concurrent=config.MAX_CONCURRENT
        )
    else:
        searcher = SyncVacancySearcher()
        details_fetcher = SyncVacancyDetailsFetcher()

    # Создание остальных компонентов
    visualizer = VacancyVisualizer()

    # Сборка pipeline
    pipeline = VacancyPipeline(
        searcher=searcher,
        details_fetcher=details_fetcher,
        analyzer_class=VacancyAnalyzer,
        visualizer=visualizer,
        output_dir=config.OUTPUT_DIR
    )

    return pipeline


def main():
    """Главная функция приложения."""
    print("\n" + "🔍 HH.RU VACANCY ANALYZER ".center(60, "="))
    print(f"Режим: {Config.MODE}")
    print(f"Парсинг: {Config.PARSING_MODE}")
    print("=" * 60 + "\n")

    # Создание pipeline через фабрику
    pipeline = create_pipeline(Config)

    # Выполнение анализа в зависимости от режима
    if Config.MODE == 'single':
        pipeline.process_single_query(
            query=Config.SINGLE_QUERY,
            area=Config.AREA,
            max_vacancies=Config.MAX_VACANCIES,
            show_plots=Config.SHOW_PLOTS,
            tech_keywords=Config.TECH_KEYWORDS
        )

    elif Config.MODE == 'batch':
        pipeline.process_batch_queries(
            queries=Config.BATCH_QUERIES,
            area=Config.AREA,
            max_vacancies=Config.MAX_VACANCIES,
            show_plots=Config.SHOW_PLOTS,
            tech_keywords=Config.TECH_KEYWORDS
        )

    else:
        print(f"❌ Неизвестный режим: {Config.MODE}")
        print("   Используйте 'single' или 'batch'")


if __name__ == "__main__":
    main()
