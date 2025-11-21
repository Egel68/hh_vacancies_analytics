from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class FetchError:
    """Модель ошибки получения данных"""
    vacancy_id: str
    error_message: str
    status_code: Optional[int]
    attempt: int
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] ID: {self.vacancy_id}, Попытка: {self.attempt}, Код: {self.status_code}, Ошибка: {self.error_message}"


class ErrorTracker:
    """
    Отслеживание ошибок при получении данных
    Single Responsibility Principle - только отслеживание ошибок
    """

    def __init__(self):
        self.errors: List[FetchError] = []
        self.errors_by_id: Dict[str, List[FetchError]] = defaultdict(list)
        self.failed_ids: set = set()
        self.successful_ids: set = set()

    def track_error(
            self,
            vacancy_id: str,
            error_message: str,
            status_code: Optional[int] = None,
            attempt: int = 1
    ) -> None:
        """Записывает ошибку"""
        error = FetchError(
            vacancy_id=vacancy_id,
            error_message=error_message,
            status_code=status_code,
            attempt=attempt
        )

        self.errors.append(error)
        self.errors_by_id[vacancy_id].append(error)
        self.failed_ids.add(vacancy_id)

    def mark_successful(self, vacancy_id: str) -> None:
        """Отмечает успешное получение данных"""
        self.successful_ids.add(vacancy_id)
        if vacancy_id in self.failed_ids:
            self.failed_ids.remove(vacancy_id)

    def get_failed_ids(self) -> List[str]:
        """Возвращает список ID с ошибками"""
        return list(self.failed_ids)

    def get_errors_for_id(self, vacancy_id: str) -> List[FetchError]:
        """Возвращает все ошибки для конкретного ID"""
        return self.errors_by_id.get(vacancy_id, [])

    def get_statistics(self) -> Dict:
        """Возвращает статистику по ошибкам"""
        status_code_counts = defaultdict(int)
        for error in self.errors:
            if error.status_code:
                status_code_counts[error.status_code] += 1

        return {
            'total_errors': len(self.errors),
            'unique_failed_ids': len(self.failed_ids),
            'successful_ids': len(self.successful_ids),
            'errors_by_status_code': dict(status_code_counts)
        }

    def print_summary(self) -> None:
        """Выводит краткую сводку по ошибкам"""
        stats = self.get_statistics()

        if stats['total_errors'] == 0:
            print("\n✅ Ошибок не обнаружено")
            return

        print(f"\n⚠️ Сводка по ошибкам:")
        print(f"   Всего ошибок: {stats['total_errors']}")
        print(f"   Неудачных ID: {stats['unique_failed_ids']}")
        print(f"   Успешных ID: {stats['successful_ids']}")

        if stats['errors_by_status_code']:
            print(f"   Ошибки по кодам:")
            for code, count in sorted(stats['errors_by_status_code'].items()):
                print(f"      {code}: {count}")
