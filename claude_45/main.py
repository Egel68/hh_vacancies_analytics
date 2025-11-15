import json
from hh_parser_async import parse_vacancies_async
from processing import VacancyAnalyzer
from pathlib import Path
from visualization import visualize_results


def main():
    """Основная функция с асинхронным парсером"""

    # Создаем папку для результатов
    output_dir = Path("./result")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Параметры парсинга
    config = {
        'query': 'Python разработчик',
        'area': 1,  # Москва (1), СПб (2), Россия (113)
        'max_vacancies': 10,
        'max_concurrent': 4  # Уменьшено для стабильности
    }

    print("=" * 60)
    print(f"🚀 Начинаем асинхронный парсинг вакансий: {config['query']}")
    print("=" * 60)

    # 1. Асинхронный парсинг вакансий
    vacancies = parse_vacancies_async(
        query=config['query'],
        area=config['area'],
        max_vacancies=config['max_vacancies'],
        max_concurrent=config['max_concurrent'],
        output_dir=str(output_dir)
    )

    if not vacancies:
        print("❌ Вакансии не найдены")
        return

    # 2. Анализ данных
    print("\n📊 Анализируем данные...")
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Имя файла на основе запроса
    safe_query = config['query'].replace(' ', '_').replace('/', '_').lower()

    # Сохранение обработанных данных
    df.to_csv(output_dir / f'{safe_query}_processed.csv', index=False, encoding='utf-8-sig')
    print(f"✅ Сохранено {len(df)} обработанных вакансий")

    # 3. Статистика
    print("\n" + "=" * 60)
    print(f"📈 СТАТИСТИКА ПО ВАКАНСИЯМ: {config['query']}")
    print("=" * 60)
    print(f"📊 Всего вакансий: {len(df)}")

    # Навыки
    print("\n📌 Топ-20 навыков:")
    print("-" * 60)
    skills_df = analyzer.analyze_skills()
    print(skills_df.head(20).to_string(index=False))
    skills_df.to_csv(output_dir / f'{safe_query}_skills.csv', index=False, encoding='utf-8-sig')

    # Требования
    print("\n📌 Топ-20 требований:")
    print("-" * 60)

    # Расширенный список ключевых слов для Python разработчика
    tech_keywords = [
        # Языки программирования
        'Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Golang', 'C++', 'C#',

        # Python фреймворки
        'Django', 'Flask', 'FastAPI', 'Tornado', 'Pyramid', 'Aiohttp',

        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'ClickHouse',
        'SQLAlchemy', 'Alembic', 'SQL',

        # Очереди и брокеры
        'RabbitMQ', 'Kafka', 'Celery', 'Redis Queue',

        # DevOps и инфраструктура
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI', 'GitHub Actions',
        'Terraform', 'Ansible', 'Linux', 'Unix',

        # Облака
        'AWS', 'Azure', 'Google Cloud', 'GCP', 'Yandex Cloud',

        # API
        'REST API', 'GraphQL', 'gRPC', 'WebSocket',

        # Тестирование
        'Pytest', 'Unittest', 'TDD', 'Unit тесты', 'Integration tests',

        # Frontend (если фулстек)
        'React', 'Vue', 'Angular', 'Node.js', 'HTML', 'CSS',

        # Архитектура
        'Microservices', 'Микросервисы', 'Monolith', 'DDD', 'SOLID',

        # Методологии
        'Agile', 'Scrum', 'Kanban',

        # Системы контроля версий
        'Git', 'GitHub', 'GitLab', 'Bitbucket',

        # Data Science / ML (если есть)
        'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Deep Learning', 'Data Science',

        # Языки
        'Английский', 'English', 'Английский язык',

        # Парсинг и скрапинг
        'Scrapy', 'BeautifulSoup', 'Selenium',

        # Асинхронность
        'Asyncio', 'Async', 'Асинхронность',

        # Веб-серверы
        'Nginx', 'Apache', 'Gunicorn', 'Uvicorn',

        # Мониторинг
        'Prometheus', 'Grafana', 'ELK', 'Sentry'
    ]

    requirements_df = analyzer.analyze_requirements(tech_keywords)
    print(requirements_df.head(20).to_string(index=False))
    requirements_df.to_csv(output_dir / f'{safe_query}_requirements.csv',
                           index=False, encoding='utf-8-sig')

    # Зарплаты
    print("\n💰 Статистика по зарплатам:")
    print("-" * 60)
    salary_stats = analyzer.get_salary_stats()
    for key, value in salary_stats.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:,.0f} ₽")
        else:
            print(f"  {key}: {value}")

    # Сохранение статистики по зарплатам
    with open(output_dir / f'{safe_query}_salary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(salary_stats, f, ensure_ascii=False, indent=2)

    # Опыт
    print("\n👔 Требуемый опыт:")
    print("-" * 60)
    exp_counts = df['experience'].value_counts()
    print(exp_counts.to_string())

    # 4. Визуализация
    print("\n📈 Создаем визуализации...")
    visualize_results(analyzer, output_dir=str(output_dir), prefix=safe_query)

    print("\n" + "=" * 60)
    print("✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 60)
    print(f"\n📁 Все результаты сохранены в папке: {output_dir.absolute()}")
    print("\n📄 Сохраненные файлы:")
    print(f"  • {safe_query}_raw.json - сырые данные")
    print(f"  • {safe_query}_processed.csv - обработанные данные")
    print(f"  • {safe_query}_skills.csv - анализ навыков")
    print(f"  • {safe_query}_requirements.csv - анализ требований")
    print(f"  • {safe_query}_salary_stats.json - статистика зарплат")
    print(f"  • {safe_query}_top_skills.png - график навыков")
    print(f"  • {safe_query}_top_requirements.png - график требований")
    print(f"  • {safe_query}_experience_distribution.png - график опыта")


if __name__ == "__main__":
    main()
