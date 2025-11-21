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
from core.retry_strategy import (
    ExponentialBackoffRetry,
    LinearRetry,
    FibonacciBackoffRetry,
    ExponentialBackoffWithJitter,
    AdaptiveRetry,
    CircuitBreakerRetry,
    IRetryStrategy
)
from typing import Optional
import sys


def create_retry_strategy(config: Config) -> IRetryStrategy:
    """
    Factory Method для создания стратегии повторных попыток

    Применяет Factory Pattern для гибкого создания объектов
    """

    strategy_map = {
        'exponential': lambda: ExponentialBackoffRetry(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            initial_delay=config.RETRY_INITIAL_DELAY,
            backoff_factor=config.RETRY_BACKOFF_FACTOR,
            max_delay=getattr(config, 'RETRY_MAX_DELAY', 120.0),
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
        'linear': lambda: LinearRetry(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            delay=config.RETRY_INITIAL_DELAY,
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
        'fibonacci': lambda: FibonacciBackoffRetry(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            initial_delay=config.RETRY_INITIAL_DELAY,
            max_delay=getattr(config, 'RETRY_MAX_DELAY', 120.0),
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
        'jitter': lambda: ExponentialBackoffWithJitter(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            initial_delay=config.RETRY_INITIAL_DELAY,
            backoff_factor=config.RETRY_BACKOFF_FACTOR,
            max_delay=getattr(config, 'RETRY_MAX_DELAY', 120.0),
            jitter_factor=getattr(config, 'RETRY_JITTER_FACTOR', 0.3),
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
        'adaptive': lambda: AdaptiveRetry(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            default_delay=config.RETRY_INITIAL_DELAY,
            rate_limit_delay=getattr(config, 'RETRY_RATE_LIMIT_DELAY', 60.0),
            server_error_backoff=config.RETRY_BACKOFF_FACTOR,
            forbidden_delay=getattr(config, 'RETRY_FORBIDDEN_DELAY', 30.0),
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
        'circuit_breaker': lambda: CircuitBreakerRetry(
            max_attempts=config.RETRY_MAX_ATTEMPTS,
            initial_delay=config.RETRY_INITIAL_DELAY,
            failure_threshold=getattr(config, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 10),
            recovery_timeout=getattr(config, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 120.0),
            retryable_status_codes=config.RETRY_STATUS_CODES
        ),
    }

    strategy_name = getattr(config, 'RETRY_STRATEGY', 'exponential').lower()

    if strategy_name not in strategy_map:
        print(f"⚠️  Неизвестная стратегия retry '{strategy_name}', используем 'exponential'")
        strategy_name = 'exponential'

    return strategy_map[strategy_name]()


def print_retry_strategy_info(strategy_name: str, config: Config) -> None:
    """Выводит информацию о выбранной стратегии retry"""

    strategy_descriptions = {
        'exponential': f"""
    📈 Экспоненциальный откат
       Задержки: {config.RETRY_INITIAL_DELAY}s → {config.RETRY_INITIAL_DELAY * config.RETRY_BACKOFF_FACTOR}s → {config.RETRY_INITIAL_DELAY * config.RETRY_BACKOFF_FACTOR ** 2}s...
       Лучше для: Rate limiting, временные проблемы сервера
       Риск: Долгое ожидание при многих попытках""",

        'linear': f"""
    📊 Линейный откат
       Задержки: {config.RETRY_INITIAL_DELAY}s → {config.RETRY_INITIAL_DELAY}s → {config.RETRY_INITIAL_DELAY}s...
       Лучше для: Кратковременные сбои, предсказуемое время
       Риск: Может перегрузить сервер""",

        'fibonacci': f"""
    🔢 Fibonacci откат
       Задержки: {config.RETRY_INITIAL_DELAY}s → {config.RETRY_INITIAL_DELAY}s → {config.RETRY_INITIAL_DELAY * 2}s → {config.RETRY_INITIAL_DELAY * 3}s...
       Лучше для: Баланс между exponential и linear
       Риск: Средняя сложность настройки""",

        'jitter': f"""
    🎲 Экспоненциальный откат с jitter
       Задержки: {config.RETRY_INITIAL_DELAY}s±{int(config.RETRY_INITIAL_DELAY * getattr(config, 'RETRY_JITTER_FACTOR', 0.3))}s → случайные интервалы
       Лучше для: Множество одновременных клиентов
       Риск: Непредсказуемое время""",

        'adaptive': f"""
    🧠 Адаптивная стратегия
       Подбирает задержку на основе типа ошибки
       429: {getattr(config, 'RETRY_RATE_LIMIT_DELAY', 60.0)}s, 403: {getattr(config, 'RETRY_FORBIDDEN_DELAY', 30.0)}s, 5xx: экспоненциально
       Лучше для: Разные типы ошибок требуют разной обработки
       Риск: Сложность реализации""",

        'circuit_breaker': f"""
    ⚡ Circuit Breaker
       Временно блокирует запросы при {getattr(config, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 10)} ошибках
       Время восстановления: {getattr(config, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 120.0)}s
       Лучше для: Защита от каскадных отказов
       Риск: Может пропустить восстановление сервера"""
    }

    description = strategy_descriptions.get(strategy_name, "    Описание недоступно")
    print(description)


def create_pipeline(config: Config) -> VacancyPipeline:
    """
    Создаёт pipeline для обработки вакансий

    Применяет Dependency Injection для гибкой конфигурации
    """

    # Создаём стратегию retry
    retry_strategy = create_retry_strategy(config)

    # Создаём компоненты на основе режима парсинга
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


def print_header(config: Config) -> None:
    """Выводит заголовок программы с настройками"""

    header = f"""
{'=' * 80}
{'🔍 HH.RU VACANCY ANALYZER':^80}
{'=' * 80}

⚙️  НАСТРОЙКИ ЗАПУСКА:
   Режим работы:        {config.MODE}
   Режим парсинга:      {config.PARSING_MODE}
   Стратегия retry:     {getattr(config, 'RETRY_STRATEGY', 'exponential')}
   Макс. попыток:       {config.RETRY_MAX_ATTEMPTS}
   Начальная задержка:  {config.RETRY_INITIAL_DELAY}s
   Backoff фактор:      {config.RETRY_BACKOFF_FACTOR}x
   """

    print(header)

    # Информация о стратегии
    print_retry_strategy_info(
        getattr(config, 'RETRY_STRATEGY', 'exponential'),
        config
    )

    # Информация о лимитах
    if config.COLLECT_ALL_VACANCIES:
        max_vacancies = None
        print(f"\n📊 Лимит вакансий:     НЕТ (собираем все доступные)")
    else:
        max_vacancies = config.MAX_VACANCIES_LIMIT
        if max_vacancies:
            print(f"\n📊 Лимит вакансий:     {max_vacancies}")
        else:
            print(f"\n📊 Лимит вакансий:     не установлен")

    print(f"   Макс. страниц:       {config.MAX_PAGES_LIMIT}")

    if config.PARSING_MODE == 'async':
        print(f"   Concurrent запросов: {config.MAX_CONCURRENT}")

    print(f"\n📁 Директория вывода:  {config.OUTPUT_DIR}")
    print(f"📈 Показывать графики: {'ДА' if config.SHOW_PLOTS else 'НЕТ'}")

    print(f"\n{'=' * 80}\n")


def print_footer(success: bool = True) -> None:
    """Выводит итоговое сообщение"""

    if success:
        footer = f"""
{'=' * 80}
{'✅ АНАЛИЗ УСПЕШНО ЗАВЕРШЁН':^80}
{'=' * 80}

💡 Проверьте директорию './result' для просмотра результатов

📊 Доступные файлы:
   • raw.json                          - Исходные данные вакансий
   • processed.csv                     - Обработанные данные
   • skills.csv                        - Анализ навыков
   • requirements.csv                  - Анализ требований
   • companies.csv                     - Топ компаний
   • salary_stats.json                 - Статистика зарплат
   • schedule.csv                      - Форматы работы
   • metro.csv                         - Распределение по метро
   • extracted_requirements_*.csv      - Извлечённые требования
   • *.png                             - Графики и визуализации

{'=' * 80}
"""
    else:
        footer = f"""
{'=' * 80}
{'❌ АНАЛИЗ ЗАВЕРШЁН С ОШИБКАМИ':^80}
{'=' * 80}

⚠️  Проверьте логи выше для деталей

💡 Возможные решения:
   1. Увеличьте RETRY_MAX_ATTEMPTS в config.py
   2. Увеличьте RETRY_INITIAL_DELAY
   3. Уменьшите MAX_CONCURRENT (для async режима)
   4. Попробуйте другую стратегию retry
   5. Проверьте интернет-соединение

{'=' * 80}
"""

    print(footer)


def print_warning() -> None:
    """Выводит предупреждение об отсутствии гарантий"""

    warning = """
⚠️  ВАЖНО: ГАРАНТИИ УСПЕШНОЙ ОБРАБОТКИ ВСЕХ ЗАПРОСОВ НЕТ!

Причины возможных ошибок:
   • Лимит повторных попыток исчерпан
   • Rate limiting API (слишком частые запросы)
   • Вакансия удалена или недоступна
   • IP-адрес временно заблокирован
   • Проблемы с сетью или интернет-соединением
   • Сервер HH.ru временно недоступен

Для максимизации успешности:
   ✓ Используйте стратегию 'jitter' для множественных запросов
   ✓ Увеличьте RETRY_MAX_ATTEMPTS до 5-7
   ✓ Уменьшите MAX_CONCURRENT до 3-5
   ✓ Увеличьте RETRY_INITIAL_DELAY до 5-10 секунд

"""
    print(warning)


def main():
    """
    Главная функция приложения.

    Координирует выполнение программы в зависимости от выбранного режима.
    """
    # Вывод заголовка и информации о конфигурации
    try:
        # Выводим заголовок
        print_header(Config)

        # Выводим предупреждение
        print_warning()

        # Определяем лимит вакансий
        if Config.COLLECT_ALL_VACANCIES:
            max_vacancies = None
        else:
            max_vacancies = Config.MAX_VACANCIES_LIMIT

        # Создаём pipeline
        print("🔧 Инициализация pipeline...")
        pipeline = create_pipeline(Config)
        print("✅ Pipeline создан успешно\n")

        # Выполняем анализ в зависимости от режима
        if Config.MODE == 'single':
            print(f"🎯 Режим: Одиночный запрос")
            print(f"🔍 Запрос: {Config.SINGLE_QUERY}\n")

            summary = pipeline.process_single_query(
                query=Config.SINGLE_QUERY,
                area=Config.AREA,
                max_vacancies=max_vacancies,
                max_pages=Config.MAX_PAGES_LIMIT,
                show_plots=Config.SHOW_PLOTS,
                tech_keywords=Config.TECH_KEYWORDS
            )

            if summary:
                print("\n" + "=" * 80)
                print("📋 КРАТКАЯ СВОДКА:")
                print("=" * 80)
                for key, value in summary.items():
                    print(f"   {key}: {value}")
                print("=" * 80 + "\n")

        elif Config.MODE == 'batch':
            print(f"🎯 Режим: Пакетная обработка")
            print(f"📦 Запросов: {len(Config.BATCH_QUERIES)}")
            print(f"📝 Список: {', '.join(Config.BATCH_QUERIES)}\n")

            summary_df = pipeline.process_batch_queries(
                queries=Config.BATCH_QUERIES,
                area=Config.AREA,
                max_vacancies=max_vacancies,
                max_pages=Config.MAX_PAGES_LIMIT,
                show_plots=Config.SHOW_PLOTS,
                tech_keywords=Config.TECH_KEYWORDS
            )

            if summary_df is not None and not summary_df.empty:
                print("\n" + "=" * 80)
                print("📋 КРАТКАЯ СВОДКА ПО ВСЕМ ЗАПРОСАМ:")
                print("=" * 80)
                print(summary_df.to_string(index=False))
                print("=" * 80 + "\n")

        else:
            print(f"❌ Неизвестный режим: {Config.MODE}")
            print("   Используйте 'single' или 'batch'")
            print_footer(success=False)
            return

        # Выводим итоговое сообщение
        print_footer(success=True)

    except KeyboardInterrupt:
        print("\n\n⚠️  Программа прервана пользователем (Ctrl+C)")
        print("   Частичные результаты могут быть сохранены в ./result")
        sys.exit(0)

    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__}")
        print(f"   Сообщение: {str(e)}")
        print("\n   Traceback:")
        import traceback
        traceback.print_exc()
        print_footer(success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
