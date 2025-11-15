"""
Главный файл для анализа вакансий с hh.ru

Поддерживает:
- Синхронный и асинхронный режимы
- Одну или несколько должностей
- Гибкую конфигурацию
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
    # Режим работы: 'single' - одна должность, 'batch' - несколько
    'mode': 'batch',  # 'single' или 'batch'

    # Тип парсинга: True - асинхронный (быстрый), False - синхронный (надежный)
    'async_mode': False,

    # Должность для анализа (если mode='single')
    'query': 'Python разработчик',

    # Список должностей (если mode='batch')
    'queries': [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer',
        'Backend разработчик'
    ],

    # Регион: 1 - Москва, 2 - СПб, 113 - Россия
    'area': 1,

    # Максимальное количество вакансий для парсинга
    'max_vacancies': 100,

    # Количество одновременных запросов (только для async)
    'max_concurrent': 4,

    # Папка для сохранения результатов
    'output_dir': './result',

    # Показывать ли графики (True/False)
    'show_plots': True,

    # Расширенный список ключевых слов для анализа требований
    'tech_keywords': [
        # Языки
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang', 'C++', 'C#', 'SQL',

        # Python фреймворки
        'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp', 'Pyramid',

        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'ClickHouse',
        'SQLAlchemy', 'Alembic',

        # Очереди
        'RabbitMQ', 'Kafka', 'Celery',

        # DevOps
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI', 'GitHub Actions',
        'Terraform', 'Ansible', 'Linux',

        # Облака
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


# ========================================
# ФУНКЦИИ
# ========================================

def analyze_single_position(config: dict):
    """Анализ одной должности"""
    query = config['query']
    safe_query = query.replace(' ', '_').replace('/', '_').lower()

    # Создаем папку для должности
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

    # Анализ
    print("\n📊 Анализируем данные...")
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение
    df.to_csv(output_dir / 'processed.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено {len(df)} обработанных вакансий")

    # Навыки
    print("\n📌 Топ-20 навыков:")
    print("-" * 60)
    skills_df = analyzer.analyze_skills()
    if len(skills_df) > 0:
        print(skills_df.head(20).to_string(index=False))
        skills_df.to_csv(output_dir / 'skills.csv', index=False, encoding='utf-8-sig')

    # Требования
    print("\n📌 Топ-20 требований:")
    print("-" * 60)
    requirements_df = analyzer.analyze_requirements(config.get('tech_keywords'))
    if len(requirements_df) > 0:
        print(requirements_df.head(20).to_string(index=False))
        requirements_df.to_csv(output_dir / 'requirements.csv', index=False, encoding='utf-8-sig')

    # Зарплаты
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

    # Опыт
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


def analyze_multiple_positions(config: dict):
    """Анализ нескольких должностей"""
    run_batch_analysis(
        queries=config['queries'],
        area=config['area'],
        max_vacancies=config['max_vacancies'],
        async_mode=config['async_mode'],
        max_concurrent=config.get('max_concurrent', 8),
        output_dir=config['output_dir']
    )


def main():
    """Главная функция"""
    print("\n" + "🔍 HH.RU VACANCY ANALYZER ".center(60, "="))
    print()

    # Выбираем режим работы
    if CONFIG['mode'] == 'single':
        analyze_single_position(CONFIG)
    elif CONFIG['mode'] == 'batch':
        analyze_multiple_positions(CONFIG)
    else:
        print(f"❌ Неизвестный режим: {CONFIG['mode']}")
        print("   Используйте 'single' или 'batch'")


if __name__ == "__main__":
    main()
