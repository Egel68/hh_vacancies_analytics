"""
Конфигурация приложения.
Централизованное хранение всех настроек.
"""

from typing import List, Optional


class Config:
    """Класс конфигурации приложения."""

    # Режим работы: 'single' или 'batch'
    MODE: str = 'batch'

    # Режим парсинга: 'sync' или 'async'
    PARSING_MODE: str = 'sync'

    # Параметры для режима 'single'
    SINGLE_QUERY: str = 'Системный аналитик'

    # Параметры для режима 'batch'
    BATCH_QUERIES: List[str] = [
        'Системный аналитик',
        'ML-инженер',
        'Бизнес аналитик'
    ]

    # Общие параметры поиска
    AREA: int = 1  # 1 - Москва, 2 - СПб, 113 - Россия

    # ========== НОВЫЕ НАСТРОЙКИ ЛИМИТОВ ==========

    # Максимальное количество вакансий для обработки (по умолчанию 1000)
    # Если None - берутся все найденные вакансии
    MAX_VACANCIES_LIMIT: Optional[int] = 50

    # Собирать ВСЕ доступные вакансии (игнорирует MAX_VACANCIES_LIMIT)
    # ВНИМАНИЕ: может занять много времени при большом количестве вакансий
    COLLECT_ALL_VACANCIES: bool = False

    # Максимальное количество страниц для парсинга (HH.ru ограничение - 20 страниц)
    # При per_page=100 это дает максимум 2000 вакансий
    MAX_PAGES_LIMIT: int = 20

    # ============================================

    MAX_CONCURRENT: int = 1  # Для асинхронного режима

    # Параметры вывода
    OUTPUT_DIR: str = './result'
    SHOW_PLOTS: bool = True

    # Ключевые слова для анализа требований
    TECH_KEYWORDS: List[str] = [
        # Языки программирования
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
        'C++', 'C#', 'SQL', 'PHP', 'Ruby', 'Rust', 'Kotlin', 'Swift',

        # Python фреймворки
        'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp', 'Pyramid',
        'Sanic', 'Bottle', 'CherryPy',

        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'ClickHouse', 'SQLAlchemy', 'Alembic', 'Oracle', 'MS SQL',
        'Cassandra', 'DynamoDB', 'Neo4j',

        # Очереди сообщений
        'RabbitMQ', 'Kafka', 'Celery', 'Redis Queue', 'SQS',

        # DevOps
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI',
        'GitHub Actions', 'Terraform', 'Ansible', 'Linux', 'Helm',
        'Prometheus', 'Grafana', 'ELK', 'Nagios',

        # Облачные платформы
        'AWS', 'Azure', 'Google Cloud', 'GCP', 'Yandex Cloud',
        'DigitalOcean', 'Heroku',

        # API
        'REST API', 'GraphQL', 'gRPC', 'WebSocket', 'Microservices',
        'SOAP', 'OpenAPI', 'Swagger',

        # Тестирование
        'Pytest', 'Unittest', 'TDD', 'BDD', 'Selenium', 'Postman',

        # Frontend
        'React', 'Vue', 'Angular', 'Node.js', 'HTML', 'CSS',
        'TypeScript', 'Webpack', 'Redux', 'Next.js',

        # Методологии
        'Agile', 'Scrum', 'Kanban', 'Git', 'Jira', 'Confluence',

        # ML/DS
        'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
        'Keras', 'Machine Learning', 'Deep Learning', 'Data Science',
        'NLP', 'Computer Vision', 'MLOps', 'Jupyter',

        # Языки
        'Английский', 'English', 'Английский язык', 'B2', 'C1',

        # Другое
        'Asyncio', 'Scrapy', 'BeautifulSoup', 'Selenium',
        'Nginx', 'Gunicorn', 'Uvicorn', 'Apache', 'Airflow'
    ]
