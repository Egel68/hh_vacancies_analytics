import requests
import time
from typing import List, Dict


class HHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {'User-Agent': 'Mozilla/5.0'}

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
                print(f"Собрано вакансий: {len(vacancies)}")

                if page >= data['pages'] - 1:
                    break

                time.sleep(0.5)  # Чтобы не нагружать сервер

            except Exception as e:
                print(f"Ошибка на странице {page}: {e}")
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
            print(f"Ошибка получения вакансии {vacancy_id}: {e}")
            return {}

    def parse_vacancies(self, query: str, area: int = 1, max_vacancies: int = 100):
        """Полный парсинг вакансий с детальной информацией"""
        print(f"Ищем вакансии: {query}")

        # Получаем список вакансий
        vacancies_list = self.search_vacancies(query, area, pages=10)
        vacancies_list = vacancies_list[:max_vacancies]

        print(f"\nПолучаем детальную информацию...")
        detailed_vacancies = []

        for i, vacancy in enumerate(vacancies_list, 1):
            details = self.get_vacancy_details(vacancy['id'])
            if details:
                detailed_vacancies.append(details)
                print(f"Обработано: {i}/{len(vacancies_list)}")
                time.sleep(0.01)

        return detailed_vacancies
