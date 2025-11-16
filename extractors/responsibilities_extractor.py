"""
Модуль извлечения обязанностей и задач из описания вакансии.
Следует принципу Single Responsibility.
"""

import re
from typing import List
from core.interfaces import ITextSectionExtractor


class ResponsibilitiesExtractor(ITextSectionExtractor):
    """
    Извлечение обязанностей и задач из текста вакансии.

    Использует паттерны для поиска секций с описанием задач
    и обязанностей кандидата.
    Следует принципу Single Responsibility - только извлечение обязанностей.
    """

    # Паттерны заголовков секций с обязанностями
    RESPONSIBILITY_HEADERS = [
        r'обязанности:?',
        r'ваши обязанности:?',
        r'в ваши обязанности входит:?',
        r'задачи:?',
        r'вам предстоит:?',
        r'чем предстоит заниматься:?',
        r'responsibilities:?',
        r'duties:?',
        r'what you.*?ll do:?',
        r'you will:?',
        r'your responsibilities:?',
        r'в работе:?',
        r'что нужно делать:?',
        r'функционал:?',
        r'основные задачи:?',
        r'чем заниматься:?',
    ]

    # Паттерны-маркеры задач
    TASK_MARKERS = [
        r'разработка',
        r'разработать',
        r'проектирование',
        r'проектировать',
        r'внедрение',
        r'внедрить',
        r'поддержка',
        r'поддерживать',
        r'оптимизация',
        r'оптимизировать',
        r'участие в',
        r'работа с',
        r'взаимодействие',
        r'создание',
        r'создавать',
        r'develop',
        r'implement',
        r'maintain',
        r'design',
        r'collaborate',
        r'build',
        r'create',
        r'support',
    ]

    def __init__(self, min_length: int = 15, max_length: int = 250):
        """
        Инициализация экстрактора.

        Args:
            min_length: Минимальная длина описания задачи
            max_length: Максимальная длина описания задачи
        """
        self.min_length = min_length
        self.max_length = max_length
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция регулярных выражений для оптимизации."""
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(' + '|'.join(self.RESPONSIBILITY_HEADERS) + r')\s*(?:\n|$)',
            re.IGNORECASE | re.MULTILINE
        )
        self.marker_pattern = re.compile(
            r'\b(' + '|'.join(self.TASK_MARKERS) + r')\b',
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[str]:
        """
        Извлечение обязанностей из текста.

        Args:
            text: Очищенный текст вакансии

        Returns:
            Список обязанностей/задач
        """
        if not text:
            return []

        responsibilities = []

        # Метод 1: Поиск по заголовкам секций
        section_resp = self._extract_from_sections(text)
        responsibilities.extend(section_resp)

        # Метод 2: Поиск по маркерам задач
        marker_resp = self._extract_by_markers(text)
        responsibilities.extend(marker_resp)

        # Метод 3: Извлечение из списков
        list_resp = self._extract_from_lists(text)
        responsibilities.extend(list_resp)

        # Очистка и дедупликация
        responsibilities = self._clean_and_deduplicate(responsibilities)

        return responsibilities

    def _extract_from_sections(self, text: str) -> List[str]:
        """
        Извлечение обязанностей из размеченных секций.
        """
        responsibilities = []

        # Поиск секции с обязанностями
        match = self.header_pattern.search(text)

        if not match:
            return responsibilities

        # Получение текста после заголовка
        section_start = match.end()

        # Поиск конца секции (следующий заголовок или конец текста)
        next_section_patterns = [
            r'\n\n(?:требования|условия|мы предлагаем|requirements|what we offer|benefits|о компании):',
        ]

        section_end = len(text)
        for pattern in next_section_patterns:
            next_match = re.search(pattern, text[section_start:], re.IGNORECASE)
            if next_match:
                section_end = section_start + next_match.start()
                break

        section_text = text[section_start:section_end]

        # Разбиение секции на элементы
        items = self._split_into_items(section_text)
        responsibilities.extend(items)

        return responsibilities

    def _extract_by_markers(self, text: str) -> List[str]:
        """
        Извлечение задач по ключевым маркерам.
        """
        responsibilities = []

        # Разбиение текста на предложения
        sentences = re.split(r'[.!?;]\s+', text)

        for sentence in sentences:
            # Проверка наличия маркеров
            if self.marker_pattern.search(sentence):
                cleaned = sentence.strip()

                # Фильтрация по длине
                if self.min_length <= len(cleaned) <= self.max_length:
                    responsibilities.append(cleaned)

        return responsibilities

    def _extract_from_lists(self, text: str) -> List[str]:
        """
        Извлечение обязанностей из маркированных и нумерованных списков.
        """
        responsibilities = []

        # Паттерны для списков
        list_patterns = [
            r'^[-•*]\s*(.+)$',  # Маркированный список
            r'^\d+[\.)]\s*(.+)$',  # Нумерованный список
        ]

        lines = text.split('\n')

        for line in lines:
            for pattern in list_patterns:
                match = re.match(pattern, line.strip(), re.MULTILINE)

                if match:
                    item = match.group(1).strip()

                    # Фильтрация по длине
                    if self.min_length <= len(item) <= self.max_length:
                        responsibilities.append(item)
                    break

        return responsibilities

    def _split_into_items(self, text: str) -> List[str]:
        """
        Разбиение текста на отдельные элементы.
        """
        items = []

        # Разбиение по различным разделителям
        separators = [';', '\n']

        current_items = [text]

        # Последовательное разбиение по разделителям
        for sep in separators:
            new_items = []
            for item in current_items:
                new_items.extend(item.split(sep))
            current_items = new_items

        # Дополнительное разбиение по точке
        final_items = []
        for item in current_items:
            parts = re.split(r'\.\s+(?=[А-ЯA-Z])', item)
            final_items.extend(parts)

        # Фильтрация и очистка
        for item in final_items:
            cleaned = item.strip()
            # Удаление начальных маркеров списка
            cleaned = re.sub(r'^[-•*\d+\.)]\s*', '', cleaned)

            if self.min_length <= len(cleaned) <= self.max_length:
                items.append(cleaned)

        return items

    def _clean_and_deduplicate(self, responsibilities: List[str]) -> List[str]:
        """
        Очистка и удаление дубликатов.
        """
        seen = set()
        unique_resp = []

        for resp in responsibilities:
            # Нормализация для сравнения
            normalized = ' '.join(resp.lower().split())

            if normalized not in seen and len(normalized) >= self.min_length:
                seen.add(normalized)
                unique_resp.append(resp)

        return unique_resp
