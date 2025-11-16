"""
Модуль синхронного парсинга вакансий с hh.ru API.

Предоставляет класс HHParser для получения данных о вакансиях
с использованием синхронных HTTP-запросов.
"""

import requests
import time
import json
from typing import List, Dict, Optional
from pathlib import Path


class HHParser:
    """
    Синхронный парсер вакансий с HeadHunter API.

    Attributes:
        base_url: Базовый URL API HH.ru
        headers: HTTP-заголовки для запросов
        output_dir: Директория для сохранения результатов
    """

    def __init__(self, output_dir: str = "./result"):
        """
        Инициализирует парсер.

        Args:
            output_dir: Путь к директории для сохранения результатов
        """
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_vacancies(
            self,
            query: str,
            area: int = 1,
            pages: int = 20
    ) -> List[Dict]:
        """
        Выполняет поиск вакансий по заданным параметрам.

        Args:
            query: Поисковый запрос (название должности)
            area: Код региона (1 - Москва, 2 - СПб, 113 - Россия)
            pages: Количество страниц для парсинга

        Returns:
            Список словарей с краткой информацией о вакансиях
        """
        vacancies = []

        for page in range(pages):
            params = {
                'text': query,
                'area': area,
                'page': page,
                'per_page': 100
            }

            try:
                response = requests.get(self.base_url, params=params, headers=self.headers)
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

    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """
        Получает детальную информацию о конкретной вакансии.

        Args:
            vacancy_id: Идентификатор вакансии

        Returns:
            Словарь с детальной информацией о вакансии или None при ошибке
        """
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Ошибка получения вакансии {vacancy_id}: {e}")
            return None

    def parse_vacancies(
            self,
            query: str,
            area: int = 1,
            max_vacancies: int = 100
    ) -> List[Dict]:
        """
        Выполняет полный парсинг вакансий с детальной информацией.

        Args:
            query: Поисковый запрос (название должности)
            area: Код региона (1 - Москва, 2 - СПб, 113 - Россия)
            max_vacancies: Максимальное количество вакансий для получения

        Returns:
            Список словарей с детальной информацией о вакансиях
        """
        print(f"🔍 Ищем вакансии: {query}")

        # Получение списка вакансий
        vacancies_list = self.search_vacancies(query, area, pages=10)
        vacancies_list = vacancies_list[:max_vacancies]

        print(f"\n📋 Получаем детальную информацию...")
        detailed_vacancies = []

        for i, vacancy in enumerate(vacancies_list, 1):
            details = self.get_vacancy_details(vacancy['id'])
            if details:
                detailed_vacancies.append(details)
                print(f"⏳ Обработано: {i}/{len(vacancies_list)} ({i / len(vacancies_list) * 100:.1f}%)")
                time.sleep(0.2)

        print(f"\n✅ Получено {len(detailed_vacancies)} детальных вакансий")
        return detailed_vacancies

    def save_to_json(self, data: any, filename: str) -> None:
        """
        Сохраняет данные в JSON-файл.

        Args:
            data: Данные для сохранения
            filename: Имя файла для сохранения
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {filepath}")


def parse_vacancies_sync(
    query: str,
    area: int = 1,
    max_vacancies: int = 100,
    output_dir: str = "./result",
    save_raw: bool = True
) -> List[Dict]:
    """
    Удобная функция-обертка для синхронного парсинга вакансий.

    Args:
        query: Поисковый запрос (название должности)
        area: Код региона (1 - Москва, 2 - СПб, 113 - Россия)
        max_vacancies: Максимальное количество вакансий для получения
        output_dir: Директория для сохранения результатов
        save_raw: Сохранять ли raw.json файл (по умолчанию True)

    Returns:
        Список словарей с детальной информацией о вакансиях
    """
    parser = HHParser(output_dir=output_dir)
    vacancies = parser.parse_vacancies(query, area, max_vacancies)

    # Сохраняем результаты только если save_raw=True
    if vacancies and save_raw:
        safe_query = query.replace(' ', '_').replace('/', '_').lower()
        parser.save_to_json(vacancies, f'{safe_query}_raw.json')

    return vacancies
