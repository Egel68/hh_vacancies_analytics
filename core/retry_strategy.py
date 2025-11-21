from abc import ABC, abstractmethod
from typing import List, Optional
import time
import random
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RetryContext:
    """Контекст для повторной попытки"""
    vacancy_id: str
    attempt: int
    last_error: Optional[Exception] = None
    last_status_code: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class IRetryStrategy(ABC):
    """Интерфейс стратегии повторных попыток (Strategy Pattern)"""

    @abstractmethod
    def should_retry(self, context: RetryContext) -> bool:
        """Определяет, нужно ли повторять попытку"""
        pass

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Возвращает задержку перед следующей попыткой"""
        pass


class ExponentialBackoffRetry(IRetryStrategy):
    """
    Стратегия экспоненциального отката

    Пример: 5s → 10s → 20s → 40s
    Используйте для: API с rate limiting, временные проблемы сервера
    """

    def __init__(
            self,
            max_attempts: int = 3,
            initial_delay: float = 5.0,
            backoff_factor: float = 2.0,
            max_delay: float = 300.0,  # Максимальная задержка
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        """Проверяет, нужно ли повторять попытку"""
        if context.attempt >= self.max_attempts:
            return False

        if context.last_status_code is not None:
            return context.last_status_code in self.retryable_status_codes

        return True

    def get_delay(self, attempt: int) -> float:
        """Вычисляет задержку с экспоненциальным откатом"""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class LinearRetry(IRetryStrategy):
    """
    Стратегия линейного отката

    Пример: 5s → 5s → 5s → 5s
    Используйте для: Кратковременные сбои, предсказуемое время выполнения
    """

    def __init__(
            self,
            max_attempts: int = 3,
            delay: float = 5.0,
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= self.max_attempts:
            return False

        if context.last_status_code is not None:
            return context.last_status_code in self.retryable_status_codes

        return True

    def get_delay(self, attempt: int) -> float:
        return self.delay


class FibonacciBackoffRetry(IRetryStrategy):
    """
    Стратегия Fibonacci отката

    Пример: 2s → 2s → 4s → 6s → 10s → 16s
    Используйте для: Баланс между exponential и linear
    """

    def __init__(
            self,
            max_attempts: int = 3,
            initial_delay: float = 2.0,
            max_delay: float = 300.0,
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]
        self._fib_sequence = [1, 1]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= self.max_attempts:
            return False

        if context.last_status_code is not None:
            return context.last_status_code in self.retryable_status_codes

        return True

    def get_delay(self, attempt: int) -> float:
        # Расширяем последовательность Фибоначчи при необходимости
        while len(self._fib_sequence) <= attempt:
            self._fib_sequence.append(
                self._fib_sequence[-1] + self._fib_sequence[-2]
            )

        delay = self.initial_delay * self._fib_sequence[attempt]
        return min(delay, self.max_delay)


class ExponentialBackoffWithJitter(IRetryStrategy):
    """
    Экспоненциальный откат с jitter (случайным шумом)

    Пример: 5s±2s → 10s±4s → 20s±8s
    Используйте для: Предотвращение "thundering herd" проблемы
    """

    def __init__(
            self,
            max_attempts: int = 3,
            initial_delay: float = 5.0,
            backoff_factor: float = 2.0,
            max_delay: float = 300.0,
            jitter_factor: float = 0.3,  # 30% случайности
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= self.max_attempts:
            return False

        if context.last_status_code is not None:
            return context.last_status_code in self.retryable_status_codes

        return True

    def get_delay(self, attempt: int) -> float:
        base_delay = self.initial_delay * (self.backoff_factor ** attempt)
        base_delay = min(base_delay, self.max_delay)

        # Добавляем случайный jitter
        jitter = base_delay * self.jitter_factor * (2 * random.random() - 1)
        delay = base_delay + jitter

        return max(0, delay)  # Гарантируем неотрицательную задержку


class AdaptiveRetry(IRetryStrategy):
    """
    Адаптивная стратегия: выбирает задержку на основе типа ошибки

    - 429 (Rate Limit): использует Retry-After заголовок или большую задержку
    - 5xx: экспоненциальный откат
    - 403: увеличенная задержка
    - Прочие: линейная задержка
    """

    def __init__(
            self,
            max_attempts: int = 3,
            default_delay: float = 5.0,
            rate_limit_delay: float = 60.0,
            server_error_backoff: float = 2.0,
            forbidden_delay: float = 30.0,
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.default_delay = default_delay
        self.rate_limit_delay = rate_limit_delay
        self.server_error_backoff = server_error_backoff
        self.forbidden_delay = forbidden_delay
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= self.max_attempts:
            return False

        if context.last_status_code is not None:
            return context.last_status_code in self.retryable_status_codes

        return True

    def get_delay(self, attempt: int, status_code: Optional[int] = None) -> float:
        if status_code == 429:
            # Rate limit - большая задержка
            return self.rate_limit_delay
        elif status_code and 500 <= status_code < 600:
            # Server errors - экспоненциальный откат
            return self.default_delay * (self.server_error_backoff ** attempt)
        elif status_code == 403:
            # Forbidden - специальная задержка
            return self.forbidden_delay
        else:
            # Прочие - стандартная задержка
            return self.default_delay


class CircuitBreakerRetry(IRetryStrategy):
    """
    Circuit Breaker: временно прекращает попытки при множественных ошибках

    Состояния:
    - CLOSED: нормальная работа
    - OPEN: слишком много ошибок, блокируем запросы
    - HALF_OPEN: пробуем восстановиться
    """

    def __init__(
            self,
            max_attempts: int = 3,
            initial_delay: float = 5.0,
            failure_threshold: int = 5,  # Порог ошибок для открытия
            recovery_timeout: float = 60.0,  # Время до попытки восстановления
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.retryable_status_codes = retryable_status_codes or [403, 429, 500, 502, 503, 504]

        # Состояние Circuit Breaker
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def should_retry(self, context: RetryContext) -> bool:
        # Проверяем состояние Circuit Breaker
        if self.state == "OPEN":
            # Проверяем, можно ли перейти в HALF_OPEN
            if (self.last_failure_time and
                    time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = "HALF_OPEN"
                print(f"🔄 Circuit Breaker: HALF_OPEN (пробуем восстановиться)")
            else:
                print(f"⛔ Circuit Breaker: OPEN (блокируем запросы)")
                return False

        if context.attempt >= self.max_attempts:
            self._record_failure()
            return False

        if context.last_status_code is not None:
            if context.last_status_code in self.retryable_status_codes:
                return True
            else:
                self._record_failure()
                return False

        return True

    def get_delay(self, attempt: int) -> float:
        return self.initial_delay * (2 ** attempt)

    def _record_failure(self):
        """Записывает ошибку и обновляет состояние"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold and self.state == "CLOSED":
            self.state = "OPEN"
            print(f"⚠️ Circuit Breaker: OPEN (слишком много ошибок: {self.failure_count})")

    def record_success(self):
        """Записывает успешный запрос"""
        if self.state == "HALF_OPEN":
            # Восстановились!
            self.state = "CLOSED"
            self.failure_count = 0
            print(f"✅ Circuit Breaker: CLOSED (восстановлено)")
        elif self.state == "CLOSED":
            # Уменьшаем счётчик ошибок при успехе
            self.failure_count = max(0, self.failure_count - 1)
