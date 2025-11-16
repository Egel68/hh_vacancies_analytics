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
            max_pages: int = 20,
            max_vacancies: Optional[int] = None
    ) -> List[Dict]:
        """
        Синхронный поиск вакансий.

        Args:
            query: Название должности
            area: Код региона
            max_pages: Максимальное количество страниц
            max_vacancies: Максимальное количество вакансий (None = все)
        """
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

                # Информация о прогрессе
                total_found = data.get('found', 0)
                print(f"📥 Собрано вакансий: {len(vacancies)} из {total_found} найденных")

                # Проверка лимита
                if max_vacancies and len(vacancies) >= max_vacancies:
                    vacancies = vacancies[:max_vacancies]
                    print(f"✋ Достигнут лимит вакансий: {max_vacancies}")
                    break

                if page >= data['pages'] - 1:
                    break

                time.sleep(0.5)

            except Exception as e:
                print(f"⚠️  Ошибка на странице {page}: {e}")
                break

        print(f"✅ Итого собрано: {len(vacancies)} вакансий")
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
            max_pages: int = 20,
            max_vacancies: Optional[int] = None
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
            self.search_async(query, area, max_pages, max_vacancies)
        )

    async def search_async(
            self,
            query: str,
            area: int = 1,
            max_pages: int = 20,
            max_vacancies: Optional[int] = None
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
            total_found = first_response.get('found', 0)
            total_pages = min(first_response.get('pages', 1), max_pages, 20)

            print(f"📊 Найдено вакансий: {total_found}")
            print(f"📄 Доступно страниц: {first_response.get('pages', 1)}")
            print(f"📄 Будет обработано страниц: {total_pages}")

            if max_vacancies:
                print(f"🎯 Лимит вакансий: {max_vacancies}")
            else:
                print(f"🎯 Лимит вакансий: не установлен (собираем все)")

            if total_pages <= 1:
                if max_vacancies and len(all_vacancies) > max_vacancies:
                    all_vacancies = all_vacancies[:max_vacancies]
                return all_vacancies

            # ========== ИСПРАВЛЕНИЕ: создаем задачи ТОЛЬКО для текущего батча ==========
            # Вместо создания всех задач сразу, создаем их пакетами
            batch_size = 5

            for page_batch_start in range(1, total_pages, batch_size):
                page_batch_end = min(page_batch_start + batch_size, total_pages)

                # Создаем задачи ТОЛЬКО для текущего батча страниц
                batch_tasks = [
                    self._fetch_page(session, query, area, page)
                    for page in range(page_batch_start, page_batch_end)
                ]

                # Выполняем только эти задачи
                results = await asyncio.gather(*batch_tasks)

                for result in results:
                    if result and 'items' in result:
                        all_vacancies.extend(result['items'])

                print(f"📥 Загружено вакансий: {len(all_vacancies)}")

                # Проверка лимита
                if max_vacancies and len(all_vacancies) >= max_vacancies:
                    all_vacancies = all_vacancies[:max_vacancies]
                    print(f"✋ Достигнут лимит вакансий: {max_vacancies}")
                    break  # Теперь break безопасен - все созданные задачи уже awaited

                # Задержка между батчами (кроме последнего)
                if page_batch_end < total_pages:
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
