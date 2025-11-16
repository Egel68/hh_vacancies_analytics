"""
Конфигурация приложения.
Централизованное хранение всех настроек.
"""

from typing import List


class Config:
    """Класс конфигурации приложения."""

    # Режим работы: 'single' или 'batch'
    MODE = 'batch'

    # Режим парсинга: 'sync' или 'async'
    PARSING_MODE = 'async'

    # Параметры для режима 'single'
    SINGLE_QUERY = 'Python разработчик'

    # Параметры для режима 'batch'
    BATCH_QUERIES = [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer',
        'Backend разработчик'
    ]

    # Общие параметры поиска
    AREA = 1  # 1 - Москва, 2 - СПб, 113 - Россия
    MAX_VACANCIES = 10
    MAX_CONCURRENT = 1  # Для асинхронного режима

    # Параметры вывода
    OUTPUT_DIR = './result'
    SHOW_PLOTS = True

    # Ключевые слова для анализа требований
    TECH_KEYWORDS: List[str] = [
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
