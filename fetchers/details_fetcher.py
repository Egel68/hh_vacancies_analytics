"""
Модуль для получения детальной информации о вакансиях.
Реализует синхронный и асинхронный режимы (Single Responsibility).
"""

import requests
import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from aiohttp import ClientSession, TCPConnector
from core.interfaces import IVacancyDetailsFetcher
from core.retry_strategy import IRetryStrategy, RetryContext
from core.error_tracker import ErrorTracker


class SyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """Синхронное получение детальной информации о вакансиях."""

    def __init__(self):
        """Инициализация fetcher'а."""
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.retry_strategy = retry_strategy
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

        detailed_vacancies = []
        ids_to_process = ids.copy()

        # Основной проход
        detailed_vacancies, failed_ids = self._fetch_batch(ids_to_process)

        # Повторные попытки для неудачных ID
        if failed_ids and self.retry_strategy:
            print(f"\n🔄 Повторная обработка {len(failed_ids)} неудачных вакансий...")
            retry_results, still_failed = self._retry_failed_ids(failed_ids)
            detailed_vacancies.extend(retry_results)

        # Вывод статистики
        self.error_tracker.print_summary()

        print(f"\n✅ Получено {len(detailed_vacancies)} из {len(ids)} вакансий")
        return detailed_vacancies

    def _fetch_batch(self, ids: List[str]) -> tuple[List[Dict], List[str]]:
        """Получает батч вакансий"""
        detailed_vacancies = []
        failed_ids = []

        for i, vacancy_id in enumerate(ids, 1):
            details = self._fetch_single_with_retry(vacancy_id)
            if details:
                detailed_vacancies.append(details)
                self.error_tracker.mark_successful(vacancy_id)
            else:
                failed_ids.append(vacancy_id)

            print(f"⏳ Обработано: {i}/{len(ids)} ({i / len(ids) * 100:.1f}%)")
            time.sleep(0.2)

        print(f"\n✅ Получено {len(detailed_vacancies)} детальных вакансий")
        return detailed_vacancies, failed_ids

    def _fetch_single_with_retry(self, vacancy_id: str) -> Optional[Dict]:
        """Получает одну вакансию с повторными попытками"""
        attempt = 0

        while True:
            context = RetryContext(
                vacancy_id=vacancy_id,
                attempt=attempt
            )

            try:
                url = f"{self.base_url}/{vacancy_id}"
                response = requests.get(url, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    return response.json()

                context.last_status_code = response.status_code

                if self.retry_strategy and self.retry_strategy.should_retry(context):
                    delay = self.retry_strategy.get_delay(attempt)
                    print(f"⚠️ Ошибка {response.status_code} для ID {vacancy_id}. Повтор через {delay:.1f}с...")

                    self.error_tracker.track_error(
                        vacancy_id,
                        f"HTTP {response.status_code}",
                        response.status_code,
                        attempt
                    )

                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    self.error_tracker.track_error(
                        vacancy_id,
                        f"HTTP {response.status_code}",
                        response.status_code,
                        attempt
                    )
                    return None

            except Exception as e:
                context.last_error = e

                if self.retry_strategy and self.retry_strategy.should_retry(context):
                    delay = self.retry_strategy.get_delay(attempt)
                    print(f"⚠️ Ошибка для ID {vacancy_id}: {str(e)}. Повтор через {delay:.1f}с...")

                    self.error_tracker.track_error(
                        vacancy_id,
                        str(e),
                        None,
                        attempt
                    )

                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    self.error_tracker.track_error(
                        vacancy_id,
                        str(e),
                        None,
                        attempt
                    )
                    return None

    def _retry_failed_ids(self, failed_ids: List[str]) -> tuple[List[Dict], List[str]]:
        """Повторно обрабатывает неудачные ID"""
        time.sleep(5)  # Пауза перед повторной обработкой
        return self._fetch_batch(failed_ids)

    def get_error_statistics(self) -> Dict:
        """Возвращает статистику по ошибкам"""
        return self.error_tracker.get_statistics()


class AsyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """
        Инициализация асинхронного fetcher'а.

        Args:
            max_concurrent: Максимальное количество одновременных запросов
        """

    def __init__(
            self,
            max_concurrent: int = 10,
            retry_strategy: Optional[IRetryStrategy] = None
    ):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'HH-User-Agent': 'VacancyParser/1.0'
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.retry_strategy = retry_strategy
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
        all_details = []
        total = len(ids)

        connector = TCPConnector(limit=30, limit_per_host=10, force_close=False)
        timeout = aiohttp.ClientTimeout(total=300, connect=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            # Основной проход
            all_details, failed_ids = await self._fetch_batch_async(
                session, ids, batch_size, total
            )

            # Повторные попытки для неудачных ID
            if failed_ids and self.retry_strategy:
                print(f"\n🔄 Повторная обработка {len(failed_ids)} неудачных вакансий...")
                await asyncio.sleep(5)  # Пауза перед повторной обработкой

                retry_results, still_failed = await self._fetch_batch_async(
                    session, failed_ids, batch_size, len(failed_ids)
                )
                all_details.extend(retry_results)

        # Вывод статистики
        self.error_tracker.print_summary()

        print(f"\n✅ Получено {len(all_details)} из {total} вакансий")
        return all_details

    async def _fetch_batch_async(
            self,
            session: ClientSession,
            ids: List[str],
            batch_size: int,
            total: int
    ) -> tuple[List[Dict], List[str]]:
        """Асинхронно получает батч вакансий"""
        all_details = []
        failed_ids = []

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]

            tasks = [
                self._fetch_single_async_with_retry(session, vac_id)
                for vac_id in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for vac_id, result in zip(batch, results):
                if isinstance(result, dict):
                    all_details.append(result)
                    self.error_tracker.mark_successful(vac_id)
                else:
                    failed_ids.append(vac_id)

            processed = min(i + batch_size, len(ids))
            percentage = processed / total * 100
            print(f"⏳ Обработано: {processed}/{total} ({percentage:.1f}%)")

            if i + batch_size < len(ids):
                await asyncio.sleep(1.0)

        print(f"\n✅ Получено {len(all_details)} детальных вакансий")
        return all_details, failed_ids

    async def _fetch_single_async_with_retry(
            self,
            session: ClientSession,
            vacancy_id: str
    ) -> Optional[Dict]:
        """Асинхронно получает одну вакансию с повторными попытками"""
        url = f"{self.base_url}/{vacancy_id}"
        attempt = 0

        while True:
            context = RetryContext(
                vacancy_id=vacancy_id,
                attempt=attempt
            )

            async with self.semaphore:
                try:
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            await asyncio.sleep(0.1)
                            return data

                        context.last_status_code = response.status

                        # Специальная обработка для 429
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            print(f"⚠️ Rate limit для ID {vacancy_id}! Ждем {retry_after}с...")
                            await asyncio.sleep(retry_after)
                            attempt += 1
                            continue

                        # Проверка на повторную попытку
                        if self.retry_strategy and self.retry_strategy.should_retry(context):
                            delay = self.retry_strategy.get_delay(attempt)

                            self.error_tracker.track_error(
                                vacancy_id,
                                f"HTTP {response.status}",
                                response.status,
                                attempt
                            )

                            await asyncio.sleep(delay)
                            attempt += 1
                            continue
                        else:
                            self.error_tracker.track_error(
                                vacancy_id,
                                f"HTTP {response.status}",
                                response.status,
                                attempt
                            )
                            return None

                except asyncio.TimeoutError as e:
                    context.last_error = e

                    if self.retry_strategy and self.retry_strategy.should_retry(context):
                        delay = self.retry_strategy.get_delay(attempt)

                        self.error_tracker.track_error(
                            vacancy_id,
                            "Timeout",
                            None,
                            attempt
                        )

                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        self.error_tracker.track_error(
                            vacancy_id,
                            "Timeout",
                            None,
                            attempt
                        )
                        return None

                except Exception as e:
                    context.last_error = e

                    if self.retry_strategy and self.retry_strategy.should_retry(context):
                        delay = self.retry_strategy.get_delay(attempt)

                        self.error_tracker.track_error(
                            vacancy_id,
                            str(e),
                            None,
                            attempt
                        )

                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        self.error_tracker.track_error(
                            vacancy_id,
                            str(e),
                            None,
                            attempt
                        )
                        print(f"⚠️  Ошибка получения вакансии {vacancy_id}: {e}")
                        return None

    def get_error_statistics(self) -> Dict:
        """Возвращает статистику по ошибкам"""
        return self.error_tracker.get_statistics()
