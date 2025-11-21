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
    # ========== ОСНОВНЫЕ НАСТРОЙКИ ==========

    # Режим работы приложения: 'single' - одна вакансия, 'batch' - несколько
    MODE: str = 'single'

    # Режим парсинга: 'sync' - синхронный, 'async' - асинхронный
    PARSING_MODE: str = 'async'

    # ==================== ЗАПРОСЫ ====================

    # Запрос для single режима
    SINGLE_QUERY: str = 'ML-инженер'

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
    MAX_VACANCIES_LIMIT: Optional[int] = 300

    # Собирать ли все доступные вакансии (игнорирует MAX_VACANCIES_LIMIT)
    COLLECT_ALL_VACANCIES: bool = False

    # Максимальное количество страниц для парсинга
    MAX_PAGES_LIMIT: int = 20

    # Максимальное количество одновременных запросов (для async режима)
    MAX_CONCURRENT: int = 10

    # ========== СТРАТЕГИИ RETRY ==========
    # Доступные стратегии: 'exponential', 'linear', 'fibonacci', 'jitter', 'adaptive', 'circuit_breaker'
    RETRY_STRATEGY: str = 'exponential'
    # Базовые настройки retry
    RETRY_MAX_ATTEMPTS: int = 5
    RETRY_INITIAL_DELAY: float = 3.0
    RETRY_BACKOFF_FACTOR: float = 2.0
    RETRY_MAX_DELAY: float = 120.0
    RETRY_STATUS_CODES: List[int] = [403, 429, 500, 502, 503, 504]

    # Настройки для Jitter стратегии
    RETRY_JITTER_FACTOR: float = 0.3  # 30% случайности

    # Настройки для Adaptive стратегии
    RETRY_RATE_LIMIT_DELAY: float = 60.0  # Задержка для 429
    RETRY_FORBIDDEN_DELAY: float = 30.0  # Задержка для 403

    # Настройки для Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 10  # Ошибок для открытия
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: float = 120.0  # Время восстановления

    # ========== ВЫВОД ==========
    OUTPUT_DIR: str = './result'
    SHOW_PLOTS: bool = False

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
