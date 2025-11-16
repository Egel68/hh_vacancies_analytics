"""
Модуль для сохранения данных в различных форматах.
Каждый класс отвечает за свой формат (Single Responsibility).
"""

import json
import pandas as pd
from pathlib import Path
from typing import Any, List, Dict
from core.interfaces import IDataSaver


class JsonSaver(IDataSaver):
    """Сохранение данных в JSON формате."""

    def save(self, data: Any, filepath: str) -> None:
        """
        Сохранение в JSON.

        Args:
            data: Данные для сохранения
            filepath: Путь к файлу
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Сохранено: {path}")


class CsvSaver(IDataSaver):
    """Сохранение данных в CSV формате."""

    def save(self, data: Any, filepath: str) -> None:
        """
        Сохранение в CSV.

        Args:
            data: DataFrame или список словарей
            filepath: Путь к файлу
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            raise ValueError("Данные должны быть DataFrame или списком словарей")

        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"💾 Сохранено: {path} ({len(df)} записей)")


class MultiFormatSaver:
    """
    Класс для сохранения данных в нескольких форматах одновременно.

    Использует композицию (Composition over Inheritance).
    """

    def __init__(self):
        """Инициализация с доступными форматами."""
        self.savers = {
            'json': JsonSaver(),
            'csv': CsvSaver()
        }

    def save(
            self,
            data: Any,
            base_filepath: str,
            formats: List[str] = None
    ) -> None:
        """
        Сохранение в несколько форматов.

        Args:
            data: Данные для сохранения
            base_filepath: Базовый путь без расширения
            formats: Список форматов ['json', 'csv']. Если None - все форматы
        """
        if formats is None:
            formats = list(self.savers.keys())

        base_path = Path(base_filepath)

        for fmt in formats:
            if fmt in self.savers:
                filepath = base_path.parent / f"{base_path.stem}.{fmt}"
                self.savers[fmt].save(data, str(filepath))
            else:
                print(f"⚠️  Неизвестный формат: {fmt}")
