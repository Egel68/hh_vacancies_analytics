from typing import List, Dict, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class FailedRequest:
    """Информация о неудачном запросе"""
    vacancy_id: str
    attempts: int
    last_error: str
    last_status_code: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ErrorTracker:
    """Отслеживание и управление неудачными запросами"""

    def __init__(self):
        self.failed_requests: Dict[str, FailedRequest] = {}
        self.successful_requests: Set[str] = set()

    def record_failure(
            self,
            vacancy_id: str,
            error: str,
            status_code: int = 0,
            attempt: int = 1
    ):
        """Записать неудачную попытку"""
        self.failed_requests[vacancy_id] = FailedRequest(
            vacancy_id=vacancy_id,
            attempts=attempt,
            last_error=error,
            last_status_code=status_code
        )

    def record_success(self, vacancy_id: str):
        """Записать успешную попытку"""
        self.successful_requests.add(vacancy_id)
        if vacancy_id in self.failed_requests:
            del self.failed_requests[vacancy_id]

    def get_failed_ids(self) -> List[str]:
        """Получить список ID неудачных запросов"""
        return list(self.failed_requests.keys())

    def get_statistics(self) -> Dict:
        """Получить статистику"""
        return {
            'total_successful': len(self.successful_requests),
            'total_failed': len(self.failed_requests),
            'success_rate': (
                len(self.successful_requests) /
                (len(self.successful_requests) + len(self.failed_requests)) * 100
                if (len(self.successful_requests) + len(self.failed_requests)) > 0
                else 0
            )
        }

    def save_failed_to_file(self, filepath: str):
        """Сохранить неудачные запросы в файл"""
        if not self.failed_requests:
            return

        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        failed_data = [
            {
                'vacancy_id': req.vacancy_id,
                'attempts': req.attempts,
                'last_error': req.last_error,
                'last_status_code': req.last_status_code,
                'timestamp': req.timestamp
            }
            for req in self.failed_requests.values()
        ]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Сохранено {len(failed_data)} неудачных запросов в {filepath}")

    def load_failed_from_file(self, filepath: str) -> List[str]:
        """Загрузить неудачные запросы из файла"""
        filepath_obj = Path(filepath)
        if not filepath_obj.exists():
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            failed_data = json.load(f)

        return [item['vacancy_id'] for item in failed_data]

    def print_summary(self):
        """Вывести сводку"""
        stats = self.get_statistics()
        print(f"\n📊 Статистика запросов:")
        print(f"   ✅ Успешно: {stats['total_successful']}")
        print(f"   ❌ Неудачно: {stats['total_failed']}")
        print(f"   📈 Процент успеха: {stats['success_rate']:.2f}%")

        if self.failed_requests:
            print(f"\n❌ Неудачные запросы:")
            for req in list(self.failed_requests.values())[:10]:
                print(f"   ID: {req.vacancy_id}, "
                      f"Попыток: {req.attempts}, "
                      f"Статус: {req.last_status_code}, "
                      f"Ошибка: {req.last_error[:50]}...")

            if len(self.failed_requests) > 10:
                print(f"   ... и еще {len(self.failed_requests) - 10}")
