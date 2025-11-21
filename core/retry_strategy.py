from abc import ABC, abstractmethod
from typing import List, Optional
import time
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
    Реализует Single Responsibility Principle
    """

    def __init__(
            self,
            max_attempts: int = 3,
            initial_delay: float = 5.0,
            backoff_factor: float = 2.0,
            retryable_status_codes: Optional[List[int]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
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
        return self.initial_delay * (self.backoff_factor ** attempt)


class LinearRetry(IRetryStrategy):
    """
    Стратегия линейного отката
    Open/Closed Principle - можем добавлять новые стратегии без изменения существующих
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
