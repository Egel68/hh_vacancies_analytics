"""
Модуль для сохранения данных в различных форматах.
Следует принципу Single Responsibility и Open/Closed.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Any
from core.interfaces import IDataSaver


class JsonSaver(IDataSaver):
    """
    Сохранение данных в формате JSON.

    Следует принципу Single Responsibility - только сохранение в JSON.
    """

    def save(self, data: Any, filepath: str) -> None:
        """
        Сохранение данных в JSON файл.

        Args:
            data: Данные для сохранения (должны быть сериализуемы в JSON)
            filepath: Путь к файлу
        """
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class CsvSaver(IDataSaver):
    """
    Сохранение данных в формате CSV.

    Следует принципу Single Responsibility - только сохранение в CSV.
    """

    def save(self, data: pd.DataFrame, filepath: str) -> None:
        """
        Сохранение DataFrame в CSV файл.

        Args:
            data: DataFrame для сохранения
            filepath: Путь к файлу
        """
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        data.to_csv(filepath, index=False, encoding='utf-8-sig')


class ExcelSaver(IDataSaver):
    """
    Сохранение данных в формате Excel.

    Демонстрирует принцип Open/Closed - новая функциональность без изменения существующих классов.
    """

    def save(self, data: pd.DataFrame, filepath: str) -> None:
        """
        Сохранение DataFrame в Excel файл.

        Args:
            data: DataFrame для сохранения
            filepath: Путь к файлу
        """
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        data.to_excel(filepath, index=False, engine='openpyxl')
