from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import time
from dataclasses import dataclass


@dataclass
class RetryContext:
    """Контекст для retry операций"""
    attempt: int
    max_attempts: int
    last_exception: Optional[Exception] = None
    status_code: Optional[int] = None


class IRetryStrategy(ABC):
    """Интерфейс стратегии повторных попыток"""

    @abstractmethod
    def should_retry(self, context: RetryContext) -> bool:
        """Определяет, нужно ли повторить попытку"""
        pass

    @abstractmethod
    def get_delay(self, context: RetryContext) -> float:
        """Возвращает задержку перед следующей попыткой"""
        pass


class ExponentialBackoffStrategy(IRetryStrategy):
    """Стратегия экспоненциального увеличения задержки"""

    def __init__(
            self,
            base_delay: float = 2.0,
            max_delay: float = 60.0,
            exponential_base: float = 2.0,
            retry_statuses: Optional[list] = None
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_statuses = retry_statuses or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= context.max_attempts:
            return False

        if context.status_code and context.status_code in self.retry_statuses:
            return True

        return False

    def get_delay(self, context: RetryContext) -> float:
        delay = self.base_delay * (self.exponential_base ** (context.attempt - 1))
        return min(delay, self.max_delay)


class LinearBackoffStrategy(IRetryStrategy):
    """Стратегия линейного увеличения задержки"""

    def __init__(
            self,
            base_delay: float = 2.0,
            max_delay: float = 60.0,
            retry_statuses: Optional[list] = None
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_statuses = retry_statuses or [403, 429, 500, 502, 503, 504]

    def should_retry(self, context: RetryContext) -> bool:
        if context.attempt >= context.max_attempts:
            return False

        if context.status_code and context.status_code in self.retry_statuses:
            return True

        return False

    def get_delay(self, context: RetryContext) -> float:
        delay = self.base_delay * context.attempt
        return min(delay, self.max_delay)


class RetryHandler:
    """Обработчик повторных попыток"""

    def __init__(self, strategy: IRetryStrategy, max_attempts: int = 5):
        self.strategy = strategy
        self.max_attempts = max_attempts

    def execute_sync(self, func, *args, **kwargs):
        """Синхронное выполнение с retry"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = RetryContext(
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    last_exception=e,
                    status_code=getattr(e, 'status_code', None)
                )

                if not self.strategy.should_retry(context):
                    raise

                delay = self.strategy.get_delay(context)
                print(f"⚠️ Попытка {attempt}/{self.max_attempts} не удалась. "
                      f"Повтор через {delay:.1f} сек...")
                time.sleep(delay)

        raise Exception(f"Превышено количество попыток ({self.max_attempts})")

    async def execute_async(self, func, *args, **kwargs):
        """Асинхронное выполнение с retry"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = RetryContext(
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    last_exception=e,
                    status_code=getattr(e, 'status_code', None)
                )

                if not self.strategy.should_retry(context):
                    raise

                delay = self.strategy.get_delay(context)
                print(f"⚠️ Попытка {attempt}/{self.max_attempts} не удалась. "
                      f"Повтор через {delay:.1f} сек...")
                await asyncio.sleep(delay)

        raise Exception(f"Превышено количество попыток ({self.max_attempts})")
