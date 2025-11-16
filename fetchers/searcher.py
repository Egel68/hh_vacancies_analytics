"""
Модуль для поиска вакансий.
Реализует синхронный и асинхронный поиск (Single Responsibility).
"""

import requests
import aiohttp
import asyncio
import time
from typing import List, Dict, Optional
from aiohttp import ClientSession, TCPConnector
from core.interfaces import IVacancySearcher


class SyncVacancySearcher(IVacancySearcher):
    """Синхронный поисковик вакансий."""

    def __init__(self):
        """Инициализация поисковика."""
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

    def search(
            self,
            query: str,
            area: int = 1,
            max_pages: int = 20
    ) -> List[Dict]:
        """Синхронный поиск вакансий."""
        print(f"🔍 Поиск вакансий: {query}")
        vacancies = []

        for page in range(max_pages):
            params = {
                'text': query,
                'area': area,
                'page': page,
                'per_page': 100
            }

            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

                if 'items' not in data:
                    break

                vacancies.extend(data['items'])
                print(f"📥 Собрано вакансий: {len(vacancies)}")

                if page >= data['pages'] - 1:
                    break

                time.sleep(0.5)

            except Exception as e:
                print(f"⚠️  Ошибка на странице {page}: {e}")
                break

        return vacancies


class AsyncVacancySearcher(IVacancySearcher):
    """Асинхронный поисковик вакансий."""

    def __init__(self, max_concurrent: int = 10):
        """
        Инициализация асинхронного поисковика.

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

    def search(
            self,
            query: str,
            area: int = 1,
            max_pages: int = 20
    ) -> List[Dict]:
        """
        Синхронная обертка для асинхронного поиска.

        Для совместимости с интерфейсом IVacancySearcher.
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
            self.search_async(query, area, max_pages)
        )

    async def search_async(
            self,
            query: str,
            area: int = 1,
            max_pages: int = 20
    ) -> List[Dict]:
        """Асинхронный поиск вакансий."""
        print(f"🔍 Асинхронный поиск вакансий: {query}")

        connector = TCPConnector(limit=30, limit_per_host=10, force_close=False)
        timeout = aiohttp.ClientTimeout(total=300, connect=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            # Получение первой страницы
            first_response = await self._fetch_page(session, query, area, 0)

            if not first_response or 'items' not in first_response:
                print("❌ Не удалось получить вакансии")
                return []

            all_vacancies = first_response['items']
            total_pages = min(first_response.get('pages', 1), max_pages, 20)

            print(f"📊 Найдено вакансий: {first_response.get('found', 0)}")
            print(f"📄 Страниц для обработки: {total_pages}")

            if total_pages <= 1:
                return all_vacancies

            # Создание задач для остальных страниц
            tasks = [
                self._fetch_page(session, query, area, page)
                for page in range(1, total_pages)
            ]

            # Выполнение пакетами
            batch_size = 5
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch)

                for result in results:
                    if result and 'items' in result:
                        all_vacancies.extend(result['items'])

                print(f"📥 Загружено вакансий: {len(all_vacancies)}")

                if i + batch_size < len(tasks):
                    await asyncio.sleep(0.5)

            print(f"✅ Всего собрано вакансий: {len(all_vacancies)}")
            return all_vacancies

    async def _fetch_page(
            self,
            session: ClientSession,
            query: str,
            area: int,
            page: int
    ) -> Optional[Dict]:
        """Получение одной страницы результатов."""
        params = {
            'text': query,
            'area': area,
            'page': page,
            'per_page': 100
        }

        async with self.semaphore:
            try:
                async with session.get(
                        self.base_url,
                        params=params,
                        headers=self.headers
                ) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        print(f"⚠️  Rate limit! Ждем {retry_after} секунд...")
                        await asyncio.sleep(retry_after)
                        return None

                    response.raise_for_status()
                    data = await response.json()
                    await asyncio.sleep(0.1)
                    return data

            except Exception as e:
                print(f"⚠️  Ошибка на странице {page}: {e}")
                return None
