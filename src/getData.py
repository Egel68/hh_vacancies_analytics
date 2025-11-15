import requests
import time
import json
from typing import List, Dict
from pathlib import Path


class HHParser:
    def __init__(self, output_dir: str = "./result"):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_vacancies(self, query: str, area: int = 1, pages: int = 20) -> List[Dict]:
        """
        Поиск вакансий
        query: название должности
        area: регион (1 - Москва, 2 - Санкт-Петербург, 113 - Россия)
        pages: количество страниц для парсинга
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

                time.sleep(0.5)  # Чтобы не нагружать сервер

            except Exception as e:
                print(f"⚠️  Ошибка на странице {page}: {e}")
                break

        return vacancies

    def get_vacancy_details(self, vacancy_id: str) -> Dict:
        """Получение детальной информации о вакансии"""
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Ошибка получения вакансии {vacancy_id}: {e}")
            return {}

    def parse_vacancies(self, query: str, area: int = 1, max_vacancies: int = 100):
        """Полный парсинг вакансий с детальной информацией"""
        print(f"🔍 Ищем вакансии: {query}")

        # Получаем список вакансий
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

    def save_to_json(self, data: any, filename: str):
        """Сохранение данных в JSON"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {filepath}")


def parse_vacancies_sync(query: str, area: int = 1,
                         max_vacancies: int = 100,
                         output_dir: str = "./result") -> List[Dict]:
    """
    Синхронный парсинг вакансий
    """
    parser = HHParser(output_dir=output_dir)
    vacancies = parser.parse_vacancies(query, area, max_vacancies)

    # Сохраняем результаты
    if vacancies:
        safe_query = query.replace(' ', '_').replace('/', '_').lower()
        parser.save_to_json(vacancies, f'{safe_query}_raw.json')

    return vacancies
