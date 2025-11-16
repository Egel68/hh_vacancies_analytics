"""
Модуль очистки текста от HTML-разметки и нормализации.
Следует принципу Single Responsibility.
"""

import re
from html import unescape
from typing import Optional
from bs4 import BeautifulSoup
from core.interfaces import ITextCleaner


class HtmlTextCleaner(ITextCleaner):
    """
    Очистка HTML-текста и приведение к читаемому виду.

    Удаляет HTML-теги, лишние пробелы, декодирует HTML-сущности.
    Следует принципу Single Responsibility - отвечает только за очистку текста.
    """

    def __init__(self, preserve_structure: bool = True):
        """
        Инициализация очистителя.

        Args:
            preserve_structure: Сохранять ли структуру документа (переводы строк)
        """
        self.preserve_structure = preserve_structure

    def clean(self, raw_text: str) -> str:
        """
        Очистка текста от HTML-разметки.

        Args:
            raw_text: Сырой HTML-текст

        Returns:
            Очищенный текст без HTML-тегов
        """
        if not raw_text:
            return ""

        # Декодирование HTML-сущностей (&nbsp;, &lt; и т.д.)
        text = unescape(raw_text)

        # Парсинг HTML с помощью BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')

        if self.preserve_structure:
            # Замена блочных элементов на переводы строк для сохранения структуры
            for element in soup.find_all(['br', 'p', 'div', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                element.replace_with('\n' + element.get_text() + '\n')

        # Извлечение текста
        clean_text = soup.get_text(separator=' ')

        # Нормализация пробелов и переводов строк
        clean_text = self._normalize_whitespace(clean_text)

        return clean_text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """
        Нормализация пробелов и переводов строк.

        Args:
            text: Текст для нормализации

        Returns:
            Нормализованный текст
        """
        # Замена множественных пробелов и табуляций на один пробел
        text = re.sub(r'[ \t]+', ' ', text)

        # Замена множественных переводов строк на двойной перевод
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # Удаление пробелов в начале и конце каждой строки
        lines = [line.strip() for line in text.split('\n')]

        # Удаление пустых строк
        lines = [line for line in lines if line]

        return '\n'.join(lines)


class SimpleTextCleaner(ITextCleaner):
    """
    Упрощенная очистка текста без использования BeautifulSoup.

    Демонстрирует принцип Open/Closed - можно добавить альтернативную
    реализацию без изменения существующего кода.
    """

    def clean(self, raw_text: str) -> str:
        """
        Простая очистка текста регулярными выражениями.

        Args:
            raw_text: Сырой HTML-текст

        Returns:
            Очищенный текст
        """
        if not raw_text:
            return ""

        # Декодирование HTML-сущностей
        text = unescape(raw_text)

        # Удаление script и style блоков
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Замена <br>, <p> и других блочных элементов на переводы строк
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?(p|div|li|tr|h\d)[^>]*>', '\n', text, flags=re.IGNORECASE)

        # Удаление всех остальных HTML-тегов
        text = re.sub(r'<[^>]+>', '', text)

        # Нормализация пробелов
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # Очистка строк
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        return '\n'.join(lines)
