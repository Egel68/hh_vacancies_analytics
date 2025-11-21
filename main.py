"""
Точка входа в приложение.
Создает и конфигурирует все компоненты согласно принципу Dependency Injection.

Следует принципу Dependency Inversion - создание зависимостей вынесено в фабрику.
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
from core.retry_strategy import ExponentialBackoffRetry


def create_pipeline(config: Config) -> VacancyPipeline:
    """
    Фабрика для создания pipeline с нужными компонентами.

    Реализует Dependency Injection - все зависимости передаются извне.
    Следует принципу Open/Closed - легко добавить новые режимы работы.

    Args:
        config: Объект конфигурации приложения

    Returns:
        VacancyPipeline: Настроенный pipeline для обработки вакансий
    """
    # Создаем стратегию повторных попыток
    retry_strategy = ExponentialBackoffRetry(
        max_attempts=config.RETRY_MAX_ATTEMPTS,
        initial_delay=config.RETRY_INITIAL_DELAY,
        backoff_factor=config.RETRY_BACKOFF_FACTOR,
        retryable_status_codes=config.RETRY_STATUS_CODES
    )

    if config.PARSING_MODE == 'async':
        searcher = AsyncVacancySearcher(max_concurrent=config.MAX_CONCURRENT)
        details_fetcher = AsyncVacancyDetailsFetcher(
            max_concurrent=config.MAX_CONCURRENT,
            retry_strategy=retry_strategy
        )
    else:
        searcher = SyncVacancySearcher()
        details_fetcher = SyncVacancyDetailsFetcher(
            retry_strategy=retry_strategy
        )

    # Создание компонента визуализации
    visualizer = VacancyVisualizer()

    # Сборка pipeline со всеми зависимостями
    pipeline = VacancyPipeline(
        searcher=searcher,
        details_fetcher=details_fetcher,
        analyzer_class=VacancyAnalyzer,
        visualizer=visualizer,
        output_dir=config.OUTPUT_DIR
    )

    return pipeline


def main():
    """
    Главная функция приложения.

    Координирует выполнение программы в зависимости от выбранного режима.
    """
    # Вывод заголовка и информации о конфигурации
    print("\n" + " 🔍 HH.RU VACANCY ANALYZER ".center(60, "="))
    print(f"Режим работы: {Config.MODE}")
    print(f"Режим парсинга: {Config.PARSING_MODE}")
    print(f"Повторных попыток: {Config.RETRY_MAX_ATTEMPTS}")
    print(f"Начальная задержка: {Config.RETRY_INITIAL_DELAY}с")

    # Определение лимита вакансий
    if Config.COLLECT_ALL_VACANCIES:
        max_vacancies = None
        print(f"Лимит вакансий: НЕТ (собираем все доступные)")
    else:
        max_vacancies = Config.MAX_VACANCIES_LIMIT
        if max_vacancies:
            print(f"Лимит вакансий: {max_vacancies}")
        else:
            print(f"Лимит вакансий: не установлен")

    print("=" * 60 + "\n")

    # Создание pipeline через фабрику
    pipeline = create_pipeline(Config)

    # Обработка в зависимости от режима
    if Config.MODE == 'single':
        # Режим анализа одной вакансии
        pipeline.process_single_query(
            query=Config.SINGLE_QUERY,
            area=Config.AREA,
            max_vacancies=max_vacancies,
            max_pages=Config.MAX_PAGES_LIMIT,
            show_plots=Config.SHOW_PLOTS,
            tech_keywords=Config.TECH_KEYWORDS
        )

    elif Config.MODE == 'batch':
        # Режим пакетного анализа нескольких вакансий
        pipeline.process_batch_queries(
            queries=Config.BATCH_QUERIES,
            area=Config.AREA,
            max_vacancies=max_vacancies,
            max_pages=Config.MAX_PAGES_LIMIT,
            show_plots=Config.SHOW_PLOTS,
            tech_keywords=Config.TECH_KEYWORDS
        )

    else:
        # Неизвестный режим
        print(f"❌ Неизвестный режим: {Config.MODE}")
        print("   Используйте 'single' или 'batch'")


if __name__ == "__main__":
    main()
