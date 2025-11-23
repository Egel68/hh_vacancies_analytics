"""
Конфигурация приложения.
Централизованное хранение всех настроек приложения для анализа вакансий HH.ru.

Следует принципу Single Responsibility - отвечает только за конфигурацию.
"""

from typing import List, Optional


class Config:
    """
    Класс конфигурации приложения.

    Все параметры объявлены как атрибуты класса для простого доступа.
    Использует type hints для явного указания типов данных.
    """

    # ==================== РЕЖИМЫ РАБОТЫ ====================

    # Режим работы приложения: 'single' - одна вакансия, 'batch' - несколько
    MODE: str = 'single'

    # Режим парсинга: 'sync' - синхронный, 'async' - асинхронный
    PARSING_MODE: str = 'sync'

    # ==================== ЗАПРОСЫ ====================

    # Запрос для single режима
    SINGLE_QUERY: str = 'Бизнес аналитик'

    # Список запросов для batch режима
    BATCH_QUERIES: List[str] = [
        'Системный аналитик',
        'ML-инженер',
        'Бизнес аналитик'
    ]

    # ==================== ПАРАМЕТРЫ ПОИСКА ====================

    # Код региона (1 - Москва, 2 - Санкт-Петербург)
    AREA: int = 1

    # Максимальное количество вакансий для сбора (None - без ограничений)
    MAX_VACANCIES_LIMIT: Optional[int] = 30

    # Собирать ли все доступные вакансии (игнорирует MAX_VACANCIES_LIMIT)
    COLLECT_ALL_VACANCIES: bool = False

    # Максимальное количество страниц для парсинга
    MAX_PAGES_LIMIT: int = 20

    # Максимальное количество одновременных запросов (для async режима)
    MAX_CONCURRENT: int = 10

    # ==================== ВЫВОД ====================

    # Директория для сохранения результатов
    OUTPUT_DIR: str = './result'

    # Показывать ли графики в окне (True) или только сохранять (False)
    SHOW_PLOTS: bool = True

    # ==================== ТЕХНИЧЕСКИЕ КЛЮЧЕВЫЕ СЛОВА ====================

    # Список технологий и навыков для анализа требований
    TECH_KEYWORDS: List[str] = [
        # Языки программирования
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Golang',
        'C++', 'C#', 'PHP', 'Ruby', 'Kotlin', 'Swift', 'R', 'Scala',

        # Web-фреймворки (Python)
        'Django', 'Flask', 'FastAPI', 'Tornado', 'Aiohttp', 'Pyramid',

        # Базы данных
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'ClickHouse', 'SQLAlchemy', 'Oracle', 'MS SQL',

        # Очереди и брокеры сообщений
        'RabbitMQ', 'Kafka', 'Celery', 'Redis Queue', 'SQS',

        # DevOps и инфраструктура
        'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab CI',
        'GitHub Actions', 'Terraform', 'Ansible', 'Linux',

        # Облачные платформы
        'AWS', 'Azure', 'Google Cloud', 'GCP', 'Yandex Cloud',

        # API и архитектура
        'REST API', 'GraphQL', 'gRPC', 'WebSocket', 'Microservices',
        'OpenAPI', 'Swagger',

        # Тестирование
        'Pytest', 'Unittest', 'TDD', 'BDD', 'Selenium', 'Postman',

        # Frontend
        'React', 'Vue', 'Angular', 'Node.js', 'HTML', 'CSS',

        # Методологии и инструменты
        'Agile', 'Scrum', 'Kanban', 'Git', 'Jira', 'Confluence',
        'BPMN', 'UML', 'IDEF',

        # Data Science и ML
        'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Data Science', 'NLP', 'LLM',

        # Аналитика и визуализация
        'Power BI', 'Tableau', 'Excel', 'Google Sheets',

        # Бизнес-системы
        'Битрикс24', 'Bitrix24', '1C', 'SAP', 'ERP', 'CRM',

        # Языки
        'Английский', 'English', 'Английский язык',
    ]

    # ==================== ПАРАМЕТРЫ ИЗВЛЕЧЕНИЯ ТРЕБОВАНИЙ ====================

    # Минимальная длина требования (символов)
    REQ_MIN_LENGTH: int = 20

    # Максимальная длина требования (символов)
    REQ_MAX_LENGTH: int = 280

    # Минимальное количество слов в требовании
    REQ_MIN_WORDS: int = 3

    # ==================== ПАРАМЕТРЫ ИЗВЛЕЧЕНИЯ ОБЯЗАННОСТЕЙ ====================

    # Минимальная длина обязанности (символов)
    RESP_MIN_LENGTH: int = 20

    # Максимальная длина обязанности (символов)
    RESP_MAX_LENGTH: int = 350

    # Минимальное количество слов в обязанности
    RESP_MIN_WORDS: int = 4

    # ==================== ПАРАМЕТРЫ ОБРАБОТКИ ====================

    # Порог схожести для дедупликации (0.0 - 1.0)
    SIMILARITY_THRESHOLD: float = 0.80

    # Использовать ли классификатор для разделения требований и обязанностей
    USE_CLASSIFIER: bool = True

    # Retry Configuration
    USE_RETRY: bool = True  # Использовать retry-механизм
    RETRY_STRATEGY_TYPE: str = 'exponential'  # 'exponential' или 'linear'
    SAVE_FAILED_REQUESTS: bool = True  # Сохранять неудачные запросы
    SHOW_DETAILED_ERRORS: bool = True  # Показывать детальные ошибки

    RETRY_MAX_ATTEMPTS: int = 5
    RETRY_BASE_DELAY: float = 2.0  # секунды
    RETRY_MAX_DELAY: float = 60.0  # секунды
    RETRY_EXPONENTIAL_BASE: float = 2.0
    RETRY_STATUSES_TO_RETRY: List[int] = [403, 429, 500, 502, 503, 504]

    # Request delays
    REQUEST_DELAY: float = 0.2
    BATCH_DELAY: float = 1.5
    ERROR_DELAY: float = 5.0
