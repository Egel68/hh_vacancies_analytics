"""
Главный файл для анализа вакансий с hh.ru.

Поддерживает:
- Синхронный и асинхронный режимы парсинга
- Анализ одной или нескольких должностей
- Гибкую конфигурацию через словарь CONFIG
"""

import json
from pathlib import Path
from getData import parse_vacancies_sync
from hh_parser_async import parse_vacancies_async
from processing import VacancyAnalyzer
from visualization import visualize_results
from batch_parser import run_batch_analysis

# ========================================
# КОНФИГУРАЦИЯ
# ========================================

CONFIG = {
    # Режим работы: 'single' - одна должность, 'batch' - несколько должностей
    'mode': 'single',
    # Использовать асинхронный режим (быстрее, но может попасть под rate limit)
    'async_mode': False,
    # Параметры для режима 'single'
    'query': 'Системный аналитик',
    # Параметры для режима 'batch'
    'queries': [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer',
        'Backend разработчик'
    ],
    # Общие параметры
    'area': 1,  # 1 - Москва, 2 - СПб, 113 - Россия
    'max_vacancies': 1000,
    'max_concurrent': 2,  # Для асинхронного режима
    'output_dir': './result',
    'show_plots': True,  # Показывать графики при создании

    # Ключевые слова для анализа требований
    'tech_keywords': [
        # Языки программирования
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
        'C++', 'C#', 'SQL',
        # Python фреймворки
        'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp', 'Pyramid',
        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'ClickHouse', 'SQLAlchemy', 'Alembic',
        # Очереди сообщений
        'RabbitMQ', 'Kafka', 'Celery',
        # DevOps
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI',
        'GitHub Actions', 'Terraform', 'Ansible', 'Linux',
        # Облачные платформы
        'AWS', 'Azure', 'Google Cloud', 'GCP', 'Yandex Cloud',
        # API
        'REST API', 'GraphQL', 'gRPC', 'WebSocket', 'Microservices',
        # Тестирование
        'Pytest', 'Unittest', 'TDD',
        # Frontend
        'React', 'Vue', 'Angular', 'Node.js', 'HTML', 'CSS',
        # Методологии
        'Agile', 'Scrum', 'Kanban', 'Git',
        # ML/DS
        'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Deep Learning', 'Data Science',
        # Языки
        'Английский', 'English', 'Английский язык',
        # Другое
        'Asyncio', 'Scrapy', 'BeautifulSoup', 'Selenium',
        'Nginx', 'Gunicorn', 'Uvicorn'
    ]
}


def analyze_single_position(config: dict) -> None:
    """
    Выполняет анализ вакансий для одной должности.

    Args:
        config: Словарь с параметрами конфигурации
    """
    query = config['query']
    safe_query = query.replace(' ', '_').replace('/', '_').lower()

    output_dir = Path(config['output_dir']) / safe_query
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"🚀 АНАЛИЗ ВАКАНСИЙ: {query}")
    print("=" * 60)
    print(f"📍 Регион: {config['area']}")
    print(f"📊 Макс. вакансий: {config['max_vacancies']}")
    print(f"⚡ Режим: {'Асинхронный' if config['async_mode'] else 'Синхронный'}")
    print("=" * 60 + "\n")

    # Парсинг вакансий
    if config['async_mode']:
        vacancies = parse_vacancies_async(
            query=query,
            area=config['area'],
            max_vacancies=config['max_vacancies'],
            max_concurrent=config['max_concurrent'],
            output_dir=str(output_dir)
        )
    else:
        vacancies = parse_vacancies_sync(
            query=query,
            area=config['area'],
            max_vacancies=config['max_vacancies'],
            output_dir=str(output_dir)
        )

    if not vacancies:
        print("❌ Вакансии не найдены")
        return

    # Анализ данных
    print("\n📊 Анализируем данные...")
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение обработанных данных
    df.to_csv(output_dir / 'processed.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено {len(df)} обработанных вакансий")

    # Анализ навыков
    print("\n📌 Топ-20 навыков:")
    print("-" * 60)
    skills_df = analyzer.analyze_skills()
    if len(skills_df) > 0:
        print(skills_df.head(20).to_string(index=False))
        skills_df.to_csv(output_dir / 'skills.csv', index=False, encoding='utf-8-sig')

    # Анализ требований
    print("\n📌 Топ-20 требований:")
    print("-" * 60)
    requirements_df = analyzer.analyze_requirements(config.get('tech_keywords'))
    if len(requirements_df) > 0:
        print(requirements_df.head(20).to_string(index=False))
        requirements_df.to_csv(output_dir / 'requirements.csv', index=False, encoding='utf-8-sig')

    # Статистика по зарплатам
    print("\n💰 Статистика по зарплатам:")
    print("-" * 60)
    salary_stats = analyzer.get_salary_stats()
    for key, value in salary_stats.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:,.0f} ₽")
        else:
            print(f"  {key}: {value}")

    with open(output_dir / 'salary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(salary_stats, f, ensure_ascii=False, indent=2)

    # Распределение по опыту
    print("\n👔 Требуемый опыт:")
    print("-" * 60)
    if 'experience' in df.columns:
        print(df['experience'].value_counts().to_string())

    # Визуализация
    print("\n📈 Создаем визуализации...")
    visualize_results(
        analyzer,
        output_dir=str(output_dir),
        prefix="",
        show_plots=config.get('show_plots', False)
    )

    # Итоговая информация
    print("\n" + "=" * 60)
    print("✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 60)
    print(f"\n📁 Результаты сохранены в: {output_dir.absolute()}")
    print("\n📄 Файлы:")
    print("  • raw.json - сырые данные")
    print("  • processed.csv - обработанные данные")
    print("  • skills.csv - анализ навыков")
    print("  • requirements.csv - анализ требований")
    print("  • salary_stats.json - статистика зарплат")
    print("  • top_skills.png - график навыков")
    print("  • top_requirements.png - график требований")
    print("  • experience_distribution.png - график опыта")


def analyze_multiple_positions(config: dict) -> None:
    """
    Выполняет анализ вакансий для нескольких должностей.

    Args:
        config: Словарь с параметрами конфигурации
    """
    run_batch_analysis(
        queries=config['queries'],
        area=config['area'],
        max_vacancies=config['max_vacancies'],
        async_mode=config['async_mode'],
        max_concurrent=config.get('max_concurrent', 8),
        output_dir=config['output_dir']
    )


def main() -> None:
    """
    Главная функция программы.

    Выбирает режим работы на основе конфигурации и запускает
    соответствующий анализ.
    """
    print("\n" + "🔍 HH.RU VACANCY ANALYZER ".center(60, "="))
    print()

    if CONFIG['mode'] == 'single':
        analyze_single_position(CONFIG)
    elif CONFIG['mode'] == 'batch':
        analyze_multiple_positions(CONFIG)
    else:
        print(f"❌ Неизвестный режим: {CONFIG['mode']}")
        print("   Используйте 'single' или 'batch'")


if __name__ == "__main__":
    main()
