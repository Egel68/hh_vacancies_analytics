"""
Модуль для получения детальной информации о вакансиях.
Реализует синхронный и асинхронный режимы (Single Responsibility).
"""

import requests
import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from aiohttp import ClientSession, TCPConnector, ClientError
from core.interfaces import IVacancyDetailsFetcher
from core.retry_strategy import (
    ExponentialBackoffStrategy,
    RetryHandler,
    RetryContext
)
from fetchers.error_tracker import ErrorTracker
from config import Config


class HTTPException(Exception):
    """Кастомное исключение для HTTP ошибок"""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class SyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """Синхронное получение детальной информации о вакансиях."""

    def __init__(
            self,
            max_attempts: int = None,
            retry_strategy: Optional[ExponentialBackoffStrategy] = None
    ):
        """Инициализация fetcher'а."""
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.max_attempts = max_attempts or Config.RETRY_MAX_ATTEMPTS

        if retry_strategy is None:
            retry_strategy = ExponentialBackoffStrategy(
                base_delay=Config.RETRY_BASE_DELAY,
                max_delay=Config.RETRY_MAX_DELAY,
                exponential_base=Config.RETRY_EXPONENTIAL_BASE,
                retry_statuses=Config.RETRY_STATUSES_TO_RETRY
            )

        self.retry_handler = RetryHandler(retry_strategy, self.max_attempts)
        self.error_tracker = ErrorTracker()

    def fetch_details(self, vacancy_ids: List[str]) -> List[Dict]:
        """
        Синхронное получение детальной информации.

        Args:
            vacancy_ids: Список ID вакансий (или список словарей с 'id')

        Returns:
            Список вакансий с детальной информацией
        """
        # Поддержка как списка ID, так и списка словарей
        if vacancy_ids and isinstance(vacancy_ids[0], dict):
            ids = [v['id'] for v in vacancy_ids]
        else:
            ids = vacancy_ids

        print(f"\n📋 Получаем детальную информацию для {len(ids)} вакансий...")
        print(f"🔄 Максимум попыток на вакансию: {self.max_attempts}")

        detailed_vacancies = []

        for i, vacancy_id in enumerate(ids, 1):
            details = self._fetch_with_retry(vacancy_id, attempt_num=1)

            if details:
                detailed_vacancies.append(details)
                self.error_tracker.record_success(vacancy_id)

            print(f"⏳ Обработано: {i}/{len(ids)} ({i / len(ids) * 100:.1f}%)")

            if i < len(ids):
                time.sleep(Config.REQUEST_DELAY)

        self.error_tracker.print_summary()

        # Повторная попытка для неудачных запросов
        failed_ids = self.error_tracker.get_failed_ids()
        if failed_ids:
            print(f"\n🔄 Повторная обработка {len(failed_ids)} неудачных запросов...")
            retry_results = self._retry_failed_requests(failed_ids)
            detailed_vacancies.extend(retry_results)

        print(f"\n✅ Получено {len(detailed_vacancies)} детальных вакансий")

        return detailed_vacancies

    def _fetch_with_retry(self, vacancy_id: str, attempt_num: int = 1) -> Optional[Dict]:
        """Получение с retry механизмом"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self._fetch_single(vacancy_id)
            except HTTPException as e:
                context = RetryContext(
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    last_exception=e,
                    status_code=e.status_code
                )

                if not self.retry_handler.strategy.should_retry(context):
                    self.error_tracker.record_failure(
                        vacancy_id,
                        str(e),
                        e.status_code,
                        attempt
                    )
                    return None

                delay = self.retry_handler.strategy.get_delay(context)

                if attempt == 1:
                    print(f"\n⚠️ Ошибка {e.status_code} для вакансии {vacancy_id}")

                print(f"   🔄 Попытка {attempt}/{self.max_attempts}, "
                      f"пауза {delay:.1f} сек...")

                time.sleep(delay)

            except Exception as e:
                self.error_tracker.record_failure(
                    vacancy_id,
                    str(e),
                    0,
                    attempt
                )
                return None

        self.error_tracker.record_failure(
            vacancy_id,
            f"Превышено количество попыток ({self.max_attempts})",
            0,
            self.max_attempts
        )
        return None

    def _fetch_single(self, vacancy_id: str) -> Optional[Dict]:
        """Получение одной вакансии."""
        url = f"{self.base_url}/{vacancy_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code in Config.RETRY_STATUSES_TO_RETRY:
                raise HTTPException(
                    f"HTTP {response.status_code}",
                    response.status_code
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            raise HTTPException(str(e), status_code)
        except requests.exceptions.RequestException as e:
            raise HTTPException(str(e), 0)

    def _retry_failed_requests(self, failed_ids: List[str]) -> List[Dict]:
        """Повторная попытка для неудачных запросов"""
        results = []

        for i, vacancy_id in enumerate(failed_ids, 1):
            print(f"   🔄 Повтор {i}/{len(failed_ids)}: {vacancy_id}")

            time.sleep(Config.ERROR_DELAY)

            details = self._fetch_with_retry(vacancy_id)
            if details:
                results.append(details)
                print(f"   ✅ Успешно получено")

        return results

    def get_error_tracker(self) -> ErrorTracker:
        """Получить трекер ошибок"""
        return self.error_tracker


class AsyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """Асинхронное получение детальной информации о вакансиях."""

    def __init__(
            self,
            max_concurrent: int = 10,
            max_attempts: int = None,
            retry_strategy: Optional[ExponentialBackoffStrategy] = None
    ):
        """
        Инициализация асинхронного fetcher'а.

        Args:
            max_concurrent: Максимальное количество одновременных запросов
        """
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'HH-User-Agent': 'VacancyParser/1.0'
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_attempts = max_attempts or Config.RETRY_MAX_ATTEMPTS

        if retry_strategy is None:
            retry_strategy = ExponentialBackoffStrategy(
                base_delay=Config.RETRY_BASE_DELAY,
                max_delay=Config.RETRY_MAX_DELAY,
                exponential_base=Config.RETRY_EXPONENTIAL_BASE,
                retry_statuses=Config.RETRY_STATUSES_TO_RETRY
            )

        self.retry_handler = RetryHandler(retry_strategy, self.max_attempts)
        self.error_tracker = ErrorTracker()

    def fetch_details(self, vacancy_ids: List[str]) -> List[Dict]:
        """
        Синхронная обертка для асинхронного получения деталей.

        Args:
            vacancy_ids: Список ID вакансий (или список словарей с 'id')

        Returns:
            Список вакансий с детальной информацией
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.fetch_details_async(vacancy_ids)
        )

    async def fetch_details_async(
            self,
            vacancy_ids: List[str],
            batch_size: int = 20
    ) -> List[Dict]:
        """Асинхронное получение детальной информации."""
        # Поддержка как списка ID, так и списка словарей
        if vacancy_ids and isinstance(vacancy_ids[0], dict):
            ids = [v['id'] for v in vacancy_ids]
        else:
            ids = vacancy_ids

        print(f"\n📋 Асинхронное получение деталей для {len(ids)} вакансий...")
        print(f"🔄 Максимум попыток на вакансию: {self.max_attempts}")
        print(f"📦 Размер батча: {batch_size}")

        all_details = []
        total = len(ids)

        connector = TCPConnector(
            limit=30,
            limit_per_host=10,
            force_close=False,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=300, connect=60, sock_read=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]

                print(f"\n📦 Обработка батча {i // batch_size + 1} "
                      f"({len(batch)} вакансий)...")

                tasks = [
                    self._fetch_with_retry_async(session, vac_id)
                    for vac_id in batch
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                batch_details = [
                    r for r in results
                    if r is not None and not isinstance(r, Exception)
                ]
                all_details.extend(batch_details)

                processed = min(i + batch_size, total)
                percentage = processed / total * 100
                print(f"⏳ Обработано: {processed}/{total} ({percentage:.1f}%)")

                if i + batch_size < len(ids):
                    await asyncio.sleep(Config.BATCH_DELAY)

        self.error_tracker.print_summary()

        # Повторная попытка для неудачных запросов
        failed_ids = self.error_tracker.get_failed_ids()
        if failed_ids:
            print(f"\n🔄 Повторная обработка {len(failed_ids)} неудачных запросов...")
            retry_results = await self._retry_failed_requests_async(failed_ids)
            all_details.extend(retry_results)

            self.error_tracker.print_summary()

        print(f"\n✅ Получено {len(all_details)} детальных вакансий")

        return all_details

    async def _fetch_with_retry_async(
            self,
            session: ClientSession,
            vacancy_id: str
    ) -> Optional[Dict]:
        """Асинхронное получение с retry механизмом"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = await self._fetch_single_async(session, vacancy_id)
                self.error_tracker.record_success(vacancy_id)
                return result

            except HTTPException as e:
                context = RetryContext(
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    last_exception=e,
                    status_code=e.status_code
                )

                if not self.retry_handler.strategy.should_retry(context):
                    self.error_tracker.record_failure(
                        vacancy_id,
                        str(e),
                        e.status_code,
                        attempt
                    )
                    return None

                delay = self.retry_handler.strategy.get_delay(context)

                if attempt == 1:
                    print(f"\n⚠️ Ошибка {e.status_code} для вакансии {vacancy_id}")

                print(f"   🔄 Попытка {attempt}/{self.max_attempts}, "
                      f"пауза {delay:.1f} сек...")

                await asyncio.sleep(delay)

            except Exception as e:
                self.error_tracker.record_failure(
                    vacancy_id,
                    str(e),
                    0,
                    attempt
                )
                return None

        self.error_tracker.record_failure(
            vacancy_id,
            f"Превышено количество попыток ({self.max_attempts})",
            0,
            self.max_attempts
        )
        return None

    async def _fetch_single_async(
            self,
            session: ClientSession,
            vacancy_id: str
    ) -> Optional[Dict]:
        """Асинхронное получение одной вакансии."""
        url = f"{self.base_url}/{vacancy_id}"

        async with self.semaphore:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status in Config.RETRY_STATUSES_TO_RETRY:
                        # Для 429 учитываем Retry-After header
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After',
                                                                   Config.RETRY_BASE_DELAY))
                            raise HTTPException(
                                f"Rate limit, retry after {retry_after}s",
                                response.status
                            )

                        raise HTTPException(
                            f"HTTP {response.status}",
                            response.status
                        )

                    response.raise_for_status()
                    data = await response.json()
                    await asyncio.sleep(0.1)
                    return data

            except aiohttp.ClientResponseError as e:
                raise HTTPException(str(e), e.status)
            except aiohttp.ClientError as e:
                raise HTTPException(str(e), 0)
            except asyncio.TimeoutError as e:
                raise HTTPException("Timeout", 0)

    async def _retry_failed_requests_async(
            self,
            failed_ids: List[str]
    ) -> List[Dict]:
        """Асинхронная повторная попытка для неудачных запросов"""
        results = []

        connector = TCPConnector(
            limit=10,
            limit_per_host=5,
            force_close=False,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=300, connect=60, sock_read=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            # Обрабатываем небольшими батчами с большими паузами
            batch_size = 5

            for i in range(0, len(failed_ids), batch_size):
                batch = failed_ids[i:i + batch_size]

                print(f"\n   🔄 Повторный батч {i // batch_size + 1} "
                      f"({len(batch)} вакансий)...")

                # Большая пауза перед повторными попытками
                await asyncio.sleep(Config.ERROR_DELAY)

                tasks = [
                    self._fetch_with_retry_async(session, vac_id)
                    for vac_id in batch
                ]

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                successful = [
                    r for r in batch_results
                    if r is not None and not isinstance(r, Exception)
                ]

                results.extend(successful)
                print(f"   ✅ Успешно получено: {len(successful)}/{len(batch)}")

        return results

    def get_error_tracker(self) -> ErrorTracker:
        """Получить трекер ошибок"""
        return self.error_tracker
