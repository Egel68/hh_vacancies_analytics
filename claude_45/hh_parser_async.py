import aiohttp
import asyncio
from typing import List, Dict, Optional
import json
from aiohttp import ClientSession, TCPConnector
import time


class HHParserAsync:
    def __init__(self, max_concurrent_requests: int = 10):
        """
        max_concurrent_requests: максимальное количество одновременных запросов
        """
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def fetch(self, session: ClientSession, url: str, params: dict = None) -> Optional[Dict]:
        """Асинхронный запрос с семафором"""
        async with self.semaphore:
            try:
                async with session.get(url, params=params, headers=self.headers) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                print(f"Ошибка запроса {url}: {e}")
                return None
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                return None

    async def search_vacancies_page(self, session: ClientSession, query: str,
                                    area: int, page: int) -> List[Dict]:
        """Поиск вакансий на одной странице"""
        params = {
            'text': query,
            'area': area,
            'page': page,
            'per_page': 100
        }

        data = await self.fetch(session, self.base_url, params)

        if data and 'items' in data:
            return data['items']
        return []

    async def search_all_vacancies(self, query: str, area: int = 1,
                                   max_pages: int = 20) -> List[Dict]:
        """Асинхронный поиск вакансий по всем страницам"""
        print(f"Ищем вакансии: {query}")

        connector = TCPConnector(limit=30, limit_per_host=30)
        async with ClientSession(connector=connector) as session:
            # Сначала получаем первую страницу, чтобы узнать общее количество
            first_page = await self.search_vacancies_page(session, query, area, 0)

            if not first_page:
                print("Не удалось получить вакансии")
                return []

            # Получаем информацию о количестве страниц
            params = {'text': query, 'area': area, 'page': 0, 'per_page': 100}
            initial_data = await self.fetch(session, self.base_url, params)

            if not initial_data:
                return first_page

            total_pages = min(initial_data.get('pages', 1), max_pages)
            print(f"Всего страниц для обработки: {total_pages}")

            # Создаем задачи для остальных страниц
            tasks = []
            for page in range(1, total_pages):
                task = self.search_vacancies_page(session, query, area, page)
                tasks.append(task)

            # Выполняем все запросы параллельно
            results = await asyncio.gather(*tasks)

            # Собираем все вакансии
            all_vacancies = first_page
            for result in results:
                if result:
                    all_vacancies.extend(result)

            print(f"Собрано вакансий: {len(all_vacancies)}")
            return all_vacancies

    async def get_vacancy_details(self, session: ClientSession,
                                  vacancy_id: str) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"
        return await self.fetch(session, url)

    async def get_vacancies_details_batch(self, vacancy_ids: List[str],
                                          batch_size: int = 50) -> List[Dict]:
        """Получение детальной информации о вакансиях пакетами"""
        all_details = []
        total = len(vacancy_ids)

        connector = TCPConnector(limit=30, limit_per_host=30)
        async with ClientSession(connector=connector) as session:
            # Разбиваем на пакеты для отображения прогресса
            for i in range(0, len(vacancy_ids), batch_size):
                batch = vacancy_ids[i:i + batch_size]

                tasks = [
                    self.get_vacancy_details(session, vac_id)
                    for vac_id in batch
                ]

                results = await asyncio.gather(*tasks)

                # Фильтруем None
                batch_details = [r for r in results if r is not None]
                all_details.extend(batch_details)

                processed = min(i + batch_size, total)
                print(f"Обработано: {processed}/{total} ({processed / total * 100:.1f}%)")

                # Небольшая пауза между пакетами
                if i + batch_size < len(vacancy_ids):
                    await asyncio.sleep(0.3)

        return all_details

    async def parse_vacancies(self, query: str, area: int = 1,
                              max_vacancies: int = 100) -> List[Dict]:
        """Полный асинхронный парсинг вакансий"""
        start_time = time.time()

        # Получаем список вакансий
        vacancies_list = await self.search_all_vacancies(query, area, max_pages=10)
        vacancies_list = vacancies_list[:max_vacancies]

        print(f"\nПолучаем детальную информацию для {len(vacancies_list)} вакансий...")

        # Получаем детальную информацию
        vacancy_ids = [v['id'] for v in vacancies_list]
        detailed_vacancies = await self.get_vacancies_details_batch(vacancy_ids)

        elapsed_time = time.time() - start_time
        print(f"\n✅ Парсинг завершен за {elapsed_time:.2f} секунд")
        print(f"Получено {len(detailed_vacancies)} детальных вакансий")

        return detailed_vacancies


# Вспомогательная функция для запуска асинхронного кода
def parse_vacancies_async(query: str, area: int = 1,
                          max_vacancies: int = 100,
                          max_concurrent: int = 10) -> List[Dict]:
    """
    Обертка для запуска асинхронного парсера

    Args:
        query: поисковый запрос
        area: регион (1-Москва, 2-СПб, 113-Россия)
        max_vacancies: максимальное количество вакансий
        max_concurrent: количество одновременных запросов
    """
    parser = HHParserAsync(max_concurrent_requests=max_concurrent)

    # Для Python 3.7+
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        parser.parse_vacancies(query, area, max_vacancies)
    )
