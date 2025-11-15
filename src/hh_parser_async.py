import aiohttp
import asyncio
from typing import List, Dict, Optional
import json
from aiohttp import ClientSession, TCPConnector
import time
from pathlib import Path


class HHParserAsync:
    def __init__(self, max_concurrent_requests: int = 10, output_dir: str = "./result"):
        """
        max_concurrent_requests: максимальное количество одновременных запросов
        output_dir: папка для сохранения результатов
        """
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'HH-User-Agent': 'VacancyParser/1.0'
        }
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Статистика запросов
        self.request_count = 0
        self.error_count = 0

    async def fetch(self, session: ClientSession, url: str, params: dict = None,
                    retry_count: int = 3, retry_delay: float = 1.0) -> Optional[Dict]:
        """Асинхронный запрос с семафором и повторными попытками"""
        async with self.semaphore:
            for attempt in range(retry_count):
                try:
                    self.request_count += 1

                    async with session.get(url, params=params, headers=self.headers,
                                           timeout=aiohttp.ClientTimeout(total=30)) as response:

                        # Обработка rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            print(f"⚠️  Rate limit! Ждем {retry_after} секунд...")
                            await asyncio.sleep(retry_after)
                            continue

                        # Обработка ошибок
                        if response.status == 403:
                            print(f"⚠️  403 Forbidden для {url}")
                            self.error_count += 1
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue

                        if response.status == 400:
                            # 400 обычно означает неверные параметры или страница не существует
                            print(f"⚠️  400 Bad Request для {url} с параметрами {params}")
                            return None

                        if response.status == 404:
                            # Вакансия не найдена или удалена
                            return None

                        response.raise_for_status()
                        data = await response.json()

                        # Небольшая задержка между запросами
                        await asyncio.sleep(0.1)

                        return data

                except aiohttp.ClientError as e:
                    print(f"⚠️  Ошибка при попытке {attempt + 1}/{retry_count}: {e}")
                    self.error_count += 1

                    if attempt < retry_count - 1:
                        delay = retry_delay * (2 ** attempt)  # Exponential backoff
                        await asyncio.sleep(delay)
                    else:
                        return None

                except asyncio.TimeoutError:
                    print(f"⚠️  Timeout для {url}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    else:
                        return None

                except Exception as e:
                    print(f"❌ Неожиданная ошибка: {e}")
                    return None

            return None

    async def search_vacancies_page(self, session: ClientSession, query: str,
                                    area: int, page: int) -> Optional[Dict]:
        """Поиск вакансий на одной странице (возвращаем весь ответ для проверки pages)"""
        params = {
            'text': query,
            'area': area,
            'page': page,
            'per_page': 100
        }

        return await self.fetch(session, self.base_url, params)

    async def search_all_vacancies(self, query: str, area: int = 1,
                                   max_pages: int = 20) -> List[Dict]:
        """Асинхронный поиск вакансий по всем страницам"""
        print(f"🔍 Ищем вакансии: {query}")

        connector = TCPConnector(limit=30, limit_per_host=10, force_close=False)
        timeout = aiohttp.ClientTimeout(total=300, connect=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            # Сначала получаем первую страницу
            first_response = await self.search_vacancies_page(session, query, area, 0)

            if not first_response or 'items' not in first_response:
                print("❌ Не удалось получить вакансии")
                return []

            all_vacancies = first_response['items']
            total_pages = min(first_response.get('pages', 1), max_pages, 20)  # API hh.ru ограничивает 20 страницами
            total_found = first_response.get('found', 0)

            print(f"📊 Найдено вакансий: {total_found}")
            print(f"📄 Страниц для обработки: {total_pages}")

            if total_pages <= 1:
                return all_vacancies

            # Создаем задачи для остальных страниц
            tasks = []
            for page in range(1, total_pages):
                task = self.search_vacancies_page(session, query, area, page)
                tasks.append(task)

            # Выполняем запросы пакетами
            batch_size = 5
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch)

                for result in results:
                    if result and 'items' in result:
                        all_vacancies.extend(result['items'])

                print(f"📥 Загружено вакансий: {len(all_vacancies)}")

                # Пауза между пакетами
                if i + batch_size < len(tasks):
                    await asyncio.sleep(0.5)

            print(f"✅ Всего собрано вакансий: {len(all_vacancies)}")
            return all_vacancies

    async def get_vacancy_details(self, session: ClientSession,
                                  vacancy_id: str) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"
        return await self.fetch(session, url)

    async def get_vacancies_details_batch(self, vacancy_ids: List[str],
                                          batch_size: int = 20) -> List[Dict]:
        """Получение детальной информации о вакансиях пакетами"""
        all_details = []
        total = len(vacancy_ids)

        print(f"\n📋 Получаем детальную информацию для {total} вакансий...")

        connector = TCPConnector(limit=30, limit_per_host=10, force_close=False)
        timeout = aiohttp.ClientTimeout(total=300, connect=60)

        async with ClientSession(connector=connector, timeout=timeout) as session:
            # Разбиваем на пакеты
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
                percentage = processed / total * 100
                print(f"⏳ Обработано: {processed}/{total} ({percentage:.1f}%)")

                # Пауза между пакетами
                if i + batch_size < len(vacancy_ids):
                    await asyncio.sleep(1.0)

        return all_details

    async def parse_vacancies(self, query: str, area: int = 1,
                              max_vacancies: int = 100) -> List[Dict]:
        """Полный асинхронный парсинг вакансий"""
        start_time = time.time()

        # Получаем список вакансий
        vacancies_list = await self.search_all_vacancies(query, area, max_pages=10)

        if not vacancies_list:
            print("❌ Вакансии не найдены")
            return []

        # Ограничиваем количество
        vacancies_list = vacancies_list[:max_vacancies]

        # Получаем детальную информацию
        vacancy_ids = [v['id'] for v in vacancies_list]
        detailed_vacancies = await self.get_vacancies_details_batch(vacancy_ids, batch_size=20)

        elapsed_time = time.time() - start_time

        print(f"\n{'=' * 60}")
        print(f"✅ Парсинг завершен за {elapsed_time:.2f} секунд")
        print(f"📊 Получено {len(detailed_vacancies)} детальных вакансий из {len(vacancy_ids)}")
        print(f"📈 Всего запросов: {self.request_count}")
        print(f"⚠️  Ошибок: {self.error_count}")
        print(f"{'=' * 60}\n")

        return detailed_vacancies

    def save_to_json(self, data: any, filename: str):
        """Сохранение данных в JSON"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {filepath}")


# Вспомогательная функция для запуска
def parse_vacancies_async(query: str, area: int = 1,
                          max_vacancies: int = 100,
                          max_concurrent: int = 10,
                          output_dir: str = "./result") -> List[Dict]:
    """
    Обертка для запуска асинхронного парсера
    """
    parser = HHParserAsync(max_concurrent_requests=max_concurrent, output_dir=output_dir)

    # Создаем или получаем event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    vacancies = loop.run_until_complete(
        parser.parse_vacancies(query, area, max_vacancies)
    )

    # Сохраняем результаты
    if vacancies:
        safe_query = query.replace(' ', '_').replace('/', '_').lower()
        parser.save_to_json(vacancies, f'{safe_query}_raw.json')

    return vacancies
