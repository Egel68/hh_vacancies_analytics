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


class SyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """Синхронное получение детальной информации о вакансиях."""

    def __init__(self):
        """Инициализация fetcher'а."""
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

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

        for i, vacancy_id in enumerate(ids, 1):
            details = self._fetch_single(vacancy_id)
            if details:
                detailed_vacancies.append(details)
                print(f"⏳ Обработано: {i}/{len(ids)} ({i / len(ids) * 100:.1f}%)")
                time.sleep(0.2)

        print(f"\n✅ Получено {len(detailed_vacancies)} детальных вакансий")
        return detailed_vacancies

    def _fetch_single(self, vacancy_id: str) -> Optional[Dict]:
        """Получение одной вакансии."""
        url = f"{self.base_url}/{vacancy_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Ошибка получения вакансии {vacancy_id}: {e}")
            return None


class AsyncVacancyDetailsFetcher(IVacancyDetailsFetcher):
    """Асинхронное получение детальной информации о вакансиях."""

    def __init__(self, max_concurrent: int = 10):
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
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]

                tasks = [
                    self._fetch_single_async(session, vac_id)
                    for vac_id in batch
                ]

                results = await asyncio.gather(*tasks)
                batch_details = [r for r in results if r is not None]
                all_details.extend(batch_details)

                processed = min(i + batch_size, total)
                percentage = processed / total * 100
                print(f"⏳ Обработано: {processed}/{total} ({percentage:.1f}%)")

                if i + batch_size < len(ids):
                    await asyncio.sleep(1.0)

        print(f"\n✅ Получено {len(all_details)} детальных вакансий")
        return all_details

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
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        await asyncio.sleep(retry_after)
                        return None

                    response.raise_for_status()
                    data = await response.json()
                    await asyncio.sleep(0.1)
                    return data

            except Exception as e:
                print(f"⚠️  Ошибка получения вакансии {vacancy_id}: {e}")
                return None
