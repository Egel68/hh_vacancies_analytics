"""
Конфигурация приложения.
Централизованное хранение всех настроек.
"""

from typing import List, Optional


class Config:
    """Класс конфигурации приложения."""

    # Режим работы: 'single' или 'batch'
    MODE: str = 'single'

    # Режим парсинга: 'sync' или 'async'
    PARSING_MODE: str = 'sync'

    # Параметры для режима 'single'
    SINGLE_QUERY: str = 'Бизнес аналитик'

    # Параметры для режима 'batch'
    BATCH_QUERIES: List[str] = [
        'Системный аналитик',
        'ML-инженер',
        'Бизнес аналитик'
    ]

    # Общие параметры поиска
    AREA: int = 1  # 1 - Москва, 2 - СПб, 113 - Россия

    # Максимальное количество вакансий для обработки
    MAX_VACANCIES_LIMIT: Optional[int] = 30

    # Собирать ВСЕ доступные вакансии
    COLLECT_ALL_VACANCIES: bool = False

    # Максимальное количество страниц для парсинга
    MAX_PAGES_LIMIT: int = 20

    MAX_CONCURRENT: int = 1

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

        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'ClickHouse', 'SQLAlchemy', 'Oracle', 'MS SQL',

        # Очереди сообщений
        'RabbitMQ', 'Kafka', 'Celery', 'Redis Queue', 'SQS',

        # DevOps
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI',
        'GitHub Actions', 'Terraform', 'Ansible', 'Linux',

        # Облачные платформы
        'AWS', 'Azure', 'Google Cloud', 'GCP', 'Yandex Cloud',

        # API
        'REST API', 'GraphQL', 'gRPC', 'WebSocket', 'Microservices',
        'OpenAPI', 'Swagger',

        # Тестирование
        'Pytest', 'Unittest', 'TDD', 'BDD', 'Selenium', 'Postman',

        # Frontend
        'React', 'Vue', 'Angular', 'Node.js', 'HTML', 'CSS',

        # Методологии
        'Agile', 'Scrum', 'Kanban', 'Git', 'Jira', 'Confluence',
        'BPMN', 'UML', 'IDEF',

        # ML/DS
        'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Data Science', 'NLP', 'LLM',

        # Бизнес-аналитика
        'Power BI', 'Tableau', 'Excel', 'Google Sheets',
        'Битрикс24', 'Bitrix24', '1C', 'SAP', 'ERP', 'CRM',

        # Языки
        'Английский', 'English', 'Английский язык',
    ]

    # ========== ПАРАМЕТРЫ ИЗВЛЕЧЕНИЯ ТРЕБОВАНИЙ ==========

    # Параметры для RequirementsExtractor
    REQ_MIN_LENGTH: int = 20
    REQ_MAX_LENGTH: int = 280
    REQ_MIN_WORDS: int = 3

    # ========== ПАРАМЕТРЫ ИЗВЛЕЧЕНИЯ ОБЯЗАННОСТЕЙ ==========

    # Параметры для ResponsibilitiesExtractor
    RESP_MIN_LENGTH: int = 20
    RESP_MAX_LENGTH: int = 350
    RESP_MIN_WORDS: int = 4

    # ========== ОБЩИЕ ПАРАМЕТРЫ ИЗВЛЕЧЕНИЯ ==========

    # Порог схожести для дедупликации (0-1)
    SIMILARITY_THRESHOLD: float = 0.80

    # Использовать классификатор для разделения требований и обязанностей
    USE_CLASSIFIER: bool = True
