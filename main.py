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
from core.retry_strategy import (
    ExponentialBackoffStrategy,
    LinearBackoffStrategy
)
from analytics.analyzer import VacancyAnalyzer
from visualization.visualizer import VacancyVisualizer
from pipeline.vacancy_pipeline import VacancyPipeline
from pathlib import Path
import sys


def create_retry_strategy(strategy_type: str = 'exponential'):
    """Создание стратегии повторных попыток"""
    if strategy_type == 'exponential':
        return ExponentialBackoffStrategy(
            base_delay=Config.RETRY_BASE_DELAY,
            max_delay=Config.RETRY_MAX_DELAY,
            exponential_base=Config.RETRY_EXPONENTIAL_BASE,
            retry_statuses=Config.RETRY_STATUSES_TO_RETRY
        )
    elif strategy_type == 'linear':
        return LinearBackoffStrategy(
            base_delay=Config.RETRY_BASE_DELAY,
            max_delay=Config.RETRY_MAX_DELAY,
            retry_statuses=Config.RETRY_STATUSES_TO_RETRY
        )
    else:
        raise ValueError(f"Неизвестный тип стратегии: {strategy_type}")


def create_pipeline(
        config: Config,
        use_retry: bool = True,
        retry_strategy_type: str = 'exponential'
) -> VacancyPipeline:
    """
    Фабрика для создания pipeline с нужными компонентами.

    Реализует Dependency Injection - все зависимости передаются извне.
    Следует принципу Open/Closed - легко добавить новые режимы работы.

    Args:
        config: Объект конфигурации приложения

    Returns:
        VacancyPipeline: Настроенный pipeline для обработки вакансий
    """

    print(f"\n⚙️  Настройка pipeline...")
    print(f"   Режим парсинга: {config.PARSING_MODE}")
    print(f"   Retry-механизм: {'✅ Включен' if use_retry else '❌ Выключен'}")

    retry_strategy = None
    if use_retry:
        retry_strategy = create_retry_strategy(retry_strategy_type)
        strategy_name = "Экспоненциальная" if retry_strategy_type == 'exponential' else "Линейная"
        print(f"   Retry-стратегия: {strategy_name}")
        print(f"   Максимум попыток: {config.RETRY_MAX_ATTEMPTS}")
        print(f"   Базовая задержка: {config.RETRY_BASE_DELAY} сек")
        print(f"   Максимальная задержка: {config.RETRY_MAX_DELAY} сек")
        print(f"   Коды для retry: {', '.join(map(str, config.RETRY_STATUSES_TO_RETRY))}")

    if config.PARSING_MODE == 'async':
        searcher = AsyncVacancySearcher(max_concurrent=config.MAX_CONCURRENT)

        if use_retry:
            details_fetcher = AsyncVacancyDetailsFetcher(
                max_concurrent=max(5, config.MAX_CONCURRENT // 2),  # Снижаем для надежности
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                retry_strategy=retry_strategy
            )
        else:
            details_fetcher = AsyncVacancyDetailsFetcher(
                max_concurrent=config.MAX_CONCURRENT
            )
    else:
        searcher = SyncVacancySearcher()

        if use_retry:
            details_fetcher = SyncVacancyDetailsFetcher(
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                retry_strategy=retry_strategy
            )
        else:
            details_fetcher = SyncVacancyDetailsFetcher()

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

    print(f"✅ Pipeline настроен и готов к работе\n")

    return pipeline


def print_header():
    """Вывод заголовка приложения"""
    print("\n" + "=" * 70)
    print(" 🔍 HH.RU VACANCY ANALYZER WITH RETRY ".center(70, "="))
    print("=" * 70)


def print_config_info(config: Config, max_vacancies):
    """Вывод информации о конфигурации"""
    print(f"\n📋 Конфигурация:")
    print(f"   Режим работы: {config.MODE}")
    print(f"   Режим парсинга: {config.PARSING_MODE}")

    if config.COLLECT_ALL_VACANCIES:
        print(f"   Лимит вакансий: ∞ (собираем все доступные)")
    else:
        if max_vacancies:
            print(f"   Лимит вакансий: {max_vacancies}")
        else:
            print(f"   Лимит вакансий: не установлен")

    print(f"   Максимум страниц: {config.MAX_PAGES_LIMIT}")
    print(f"   Concurrent запросы: {config.MAX_CONCURRENT}")
    print(f"   Использовать классификатор: {'Да' if config.USE_CLASSIFIER else 'Нет'}")
    print(f"   Показывать графики: {'Да' if config.SHOW_PLOTS else 'Нет'}")


def save_error_statistics(pipeline: VacancyPipeline, output_dir: str):
    """Сохранение статистики ошибок"""
    if hasattr(pipeline.details_fetcher, 'get_error_tracker'):
        error_tracker = pipeline.details_fetcher.get_error_tracker()

        failed_ids = error_tracker.get_failed_ids()
        if failed_ids:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            error_tracker.save_failed_to_file(
                str(output_path / 'failed_requests.json')
            )

            print(f"\n⚠️  Обнаружены неудачные запросы: {len(failed_ids)}")
            print(f"   Сохранены в: {output_path / 'failed_requests.json'}")


def print_final_summary(summary: dict):
    """Вывод итоговой сводки для single режима"""
    if not summary:
        return

    print("\n" + "=" * 70)
    print(" 📊 ИТОГОВАЯ СВОДКА ".center(70, "="))
    print("=" * 70)

    print(f"\n🎯 Должность: {summary.get('Должность', 'N/A')}")
    print(f"📦 Вакансий собрано: {summary.get('Вакансий собрано', 0)}")

    if summary.get('Топ-5 навыков'):
        print(f"\n🔧 Топ-5 навыков:")
        skills = summary.get('Топ-5 навыков', '').split(', ')
        for i, skill in enumerate(skills[:5], 1):
            if skill:
                print(f"   {i}. {skill}")

    if summary.get('Топ-3 компании'):
        print(f"\n🏢 Топ-3 компании:")
        companies = summary.get('Топ-3 компании', '').split(', ')
        for i, company in enumerate(companies[:3], 1):
            if company:
                print(f"   {i}. {company}")

    avg_salary = summary.get('Средняя ЗП (от)')
    median_salary = summary.get('Медиана ЗП (от)')

    if avg_salary and avg_salary != 'N/A':
        print(f"\n💰 Зарплата:")
        print(f"   Средняя (от): {avg_salary:,.0f} руб.")
        if median_salary and median_salary != 'N/A':
            print(f"   Медиана (от): {median_salary:,.0f} руб.")

    if summary.get('Извлечено требований'):
        print(f"\n📝 Обработка описаний:")
        print(f"   Требований: {summary.get('Извлечено требований', 0)}")
        print(f"   Обязанностей: {summary.get('Извлечено обязанностей', 0)}")

    print(f"\n📁 Результаты: {summary.get('Папка', 'N/A')}")
    print("=" * 70)


def print_batch_summary(summary_df):
    """Вывод итоговой сводки для batch режима"""
    print("\n" + "=" * 70)
    print(" 📊 СВОДКА ПО ВСЕМ ЗАПРОСАМ ".center(70, "="))
    print("=" * 70)

    total_vacancies = summary_df['Вакансий собрано'].sum()
    avg_vacancies = summary_df['Вакансий собрано'].mean()

    print(f"\n📊 Общая статистика:")
    print(f"   Всего вакансий: {total_vacancies}")
    print(f"   Обработано запросов: {len(summary_df)}")
    print(f"   Среднее на запрос: {avg_vacancies:.1f}")

    print(f"\n📋 По каждому запросу:")
    print(f"   {'№':<4} {'Должность':<30} {'Вакансий':<10} {'Средняя ЗП':<15}")
    print(f"   {'-' * 4} {'-' * 30} {'-' * 10} {'-' * 15}")

    for idx, row in summary_df.iterrows():
        salary_str = 'N/A'
        if row.get('Средняя ЗП (от)') and row['Средняя ЗП (от)'] != 'N/A':
            salary_str = f"{row['Средняя ЗП (от)']:,.0f}"

        position = row['Должность'][:28] + '..' if len(row['Должность']) > 30 else row['Должность']

        print(f"   {idx + 1:<4} {position:<30} {row['Вакансий собрано']:<10} {salary_str:<15}")

    print("=" * 70)


def main():
    """
    Главная функция приложения.

    Координирует выполнение программы в зависимости от выбранного режима.
    """
    # Вывод заголовка и информации о конфигурации
    print_header()

    # Определяем параметры из Config
    use_retry = getattr(AppConfig, 'USE_RETRY', True)
    retry_strategy_type = getattr(AppConfig, 'RETRY_STRATEGY_TYPE', 'exponential')

    # Определяем максимальное количество вакансий
    if Config.COLLECT_ALL_VACANCIES:
        max_vacancies = None
    else:
        max_vacancies = Config.MAX_VACANCIES_LIMIT

    print_config_info(Config, max_vacancies)

    # Создаем pipeline
    pipeline = create_pipeline(
        Config,
        use_retry=use_retry,
        retry_strategy_type=retry_strategy_type
    )

    try:
        if Config.MODE == 'single':
            print(f"\n🎯 Запуск анализа: '{Config.SINGLE_QUERY}'")
            print("=" * 70 + "\n")

            summary = pipeline.process_single_query(
                query=Config.SINGLE_QUERY,
                area=Config.AREA,
                max_vacancies=max_vacancies,
                max_pages=Config.MAX_PAGES_LIMIT,
                show_plots=Config.SHOW_PLOTS,
                tech_keywords=Config.TECH_KEYWORDS
            )

            # Сохраняем статистику ошибок
            if summary:
                save_error_statistics(
                    pipeline,
                    summary.get('Папка', Config.OUTPUT_DIR)
                )
                print_final_summary(summary)

        elif Config.MODE == 'batch':
            print(f"\n🎯 Пакетный анализ: {len(Config.BATCH_QUERIES)} запросов")
            print("=" * 70 + "\n")

            summary_df = pipeline.process_batch_queries(
                queries=Config.BATCH_QUERIES,
                area=Config.AREA,
                max_vacancies=max_vacancies,
                max_pages=Config.MAX_PAGES_LIMIT,
                show_plots=Config.SHOW_PLOTS,
                tech_keywords=Config.TECH_KEYWORDS
            )

            save_error_statistics(pipeline, Config.OUTPUT_DIR)

            if not summary_df.empty:
                print_batch_summary(summary_df)

        else:
            print(f"\n❌ Неизвестный режим: {Config.MODE}")
            print("   Используйте 'single' или 'batch'")
            sys.exit(1)

        print("\n" + "=" * 70)
        print(" ✅ РАБОТА ЗАВЕРШЕНА УСПЕШНО ".center(70, "="))
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Работа прервана пользователем (Ctrl+C)")
        print("   Сохраняем статистику ошибок...")
        save_error_statistics(pipeline, Config.OUTPUT_DIR)
        print("   ✅ Статистика сохранена")
        sys.exit(0)

    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {type(e).__name__}")
        print(f"   Сообщение: {str(e)}")

        if getattr(AppConfig, 'SHOW_DETAILED_ERRORS', False):
            import traceback
            print("\n📋 Детальная информация об ошибке:")
            traceback.print_exc()

        print("\n   Сохраняем статистику ошибок...")
        save_error_statistics(pipeline, Config.OUTPUT_DIR)
        print("   ✅ Статистика сохранена")

        sys.exit(1)


if __name__ == "__main__":
    main()
