"""
Модуль извлечения требований к кандидату из текста описания.
Следует принципу Single Responsibility и Open/Closed.
"""

import re
from typing import List, Set, Dict
from core.interfaces import ITextSectionExtractor


class RequirementsExtractor(ITextSectionExtractor):
    """
    Извлечение требований к кандидату из текста вакансии.

    Использует паттерны для поиска секций с требованиями
    и извлекает структурированную информацию.
    Следует принципу Single Responsibility - только извлечение требований.
    """

    # Паттерны заголовков секций с требованиями
    REQUIREMENT_HEADERS = [
        r'требования:?',
        r'требуем:?',
        r'мы ожидаем:?',
        r'ожидаем от кандидата:?',
        r'кандидат должен:?',
        r'необходим[оыа]:?',
        r'необходимые навыки:?',
        r'что мы ожидаем:?',
        r'что нужно:?',
        r'requirements:?',
        r'must have:?',
        r'qualifications:?',
        r'нам важно:?',
        r'мы ищем:?',
        r'идеальный кандидат:?',
        r'вы нам подходите:?',
        r'технические требования:?',
        r'hard skills:?',
    ]

    # Паттерны-маркеры требований внутри текста
    REQUIREMENT_MARKERS = [
        r'опыт работы',
        r'знание',
        r'владение',
        r'умение',
        r'навык[ии]',
        r'понимание',
        r'experience',
        r'knowledge',
        r'understanding',
        r'proficiency',
        r'familiar with',
        r'expertise',
    ]

    def __init__(self, min_length: int = 10, max_length: int = 200):
        """
        Инициализация экстрактора.

        Args:
            min_length: Минимальная длина требования (символов)
            max_length: Максимальная длина требования (символов)
        """
        self.min_length = min_length
        self.max_length = max_length
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция регулярных выражений для оптимизации."""
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(' + '|'.join(self.REQUIREMENT_HEADERS) + r')\s*(?:\n|$)',
            re.IGNORECASE | re.MULTILINE
        )
        self.marker_pattern = re.compile(
            r'\b(' + '|'.join(self.REQUIREMENT_MARKERS) + r')\b',
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[str]:
        """
        Извлечение требований из текста.

        Args:
            text: Очищенный текст вакансии

        Returns:
            Список требований (строки)
        """
        if not text:
            return []

        requirements = []

        # Метод 1: Поиск по заголовкам секций
        section_requirements = self._extract_from_sections(text)
        requirements.extend(section_requirements)

        # Метод 2: Поиск по маркерам в тексте
        marker_requirements = self._extract_by_markers(text)
        requirements.extend(marker_requirements)

        # Метод 3: Извлечение из списков
        list_requirements = self._extract_from_lists(text)
        requirements.extend(list_requirements)

        # Очистка и дедупликация
        requirements = self._clean_and_deduplicate(requirements)

        return requirements

    def _extract_from_sections(self, text: str) -> List[str]:
        """
        Извлечение требований из размеченных секций.

        Ищет секции, начинающиеся с заголовков типа "Требования:"
        """
        requirements = []

        # Поиск секции с требованиями
        match = self.header_pattern.search(text)

        if not match:
            return requirements

        # Получение текста после заголовка
        section_start = match.end()

        # Поиск конца секции (следующий заголовок или конец текста)
        next_section_patterns = [
            r'\n\n(?:обязанности|задачи|responsibilities|условия|мы предлагаем|what we offer|benefits|о компании):',
        ]

        section_end = len(text)
        for pattern in next_section_patterns:
            next_match = re.search(pattern, text[section_start:], re.IGNORECASE)
            if next_match:
                section_end = section_start + next_match.start()
                break

        section_text = text[section_start:section_end]

        # Разбиение секции на отдельные элементы
        items = self._split_into_items(section_text)
        requirements.extend(items)

        return requirements

    def _extract_by_markers(self, text: str) -> List[str]:
        """
        Извлечение требований по ключевым маркерам.

        Ищет предложения, содержащие маркеры типа "опыт работы", "знание" и т.д.
        """
        requirements = []

        # Разбиение текста на предложения
        sentences = re.split(r'[.!?;]\s+', text)

        for sentence in sentences:
            # Проверка наличия маркеров
            if self.marker_pattern.search(sentence):
                cleaned = sentence.strip()

                # Фильтрация по длине
                if self.min_length <= len(cleaned) <= self.max_length:
                    requirements.append(cleaned)

        return requirements

    def _extract_from_lists(self, text: str) -> List[str]:
        """
        Извлечение требований из маркированных и нумерованных списков.
        """
        requirements = []

        # Паттерны для списков
        list_patterns = [
            r'^[-•*]\s*(.+)$',  # Маркированный список: - item
            r'^\d+[\.)]\s*(.+)$',  # Нумерованный список: 1. item или 1) item
        ]

        lines = text.split('\n')

        for line in lines:
            for pattern in list_patterns:
                match = re.match(pattern, line.strip(), re.MULTILINE)

                if match:
                    item = match.group(1).strip()

                    # Фильтрация по длине
                    if self.min_length <= len(item) <= self.max_length:
                        requirements.append(item)
                    break  # Одно совпадение на строку

        return requirements

    def _split_into_items(self, text: str) -> List[str]:
        """
        Разбиение текста на отдельные элементы.

        Использует различные разделители: точка с запятой, перевод строки, точка.
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

        # Дополнительное разбиение по точке (осторожно, чтобы не разбить аббревиатуры)
        final_items = []
        for item in current_items:
            # Разбиение по точке, если после точки заглавная буква
            parts = re.split(r'\.\s+(?=[А-ЯA-Z])', item)
            final_items.extend(parts)

        # Фильтрация и очистка
        for item in final_items:
            cleaned = item.strip()
            # Удаление начальных маркеров списка, если остались
            cleaned = re.sub(r'^[-•*\d+\.)]\s*', '', cleaned)

            if self.min_length <= len(cleaned) <= self.max_length:
                items.append(cleaned)

        return items

    def _clean_and_deduplicate(self, requirements: List[str]) -> List[str]:
        """
        Очистка и удаление дубликатов из списка требований.
        """
        # Удаление дубликатов с сохранением порядка
        seen = set()
        unique_requirements = []

        for req in requirements:
            # Нормализация для сравнения (нижний регистр, без лишних пробелов)
            normalized = ' '.join(req.lower().split())

            if normalized not in seen and len(normalized) >= self.min_length:
                seen.add(normalized)
                unique_requirements.append(req)

        return unique_requirements


class SkillsBasedRequirementsExtractor(RequirementsExtractor):
    """
    Расширенный экстрактор с фокусом на технические навыки.

    Демонстрирует принцип Open/Closed - расширение базовой функциональности
    без модификации базового класса.
    Принцип Liskov Substitution - можно использовать вместо базового класса.
    """

    def __init__(
            self,
            tech_keywords: List[str],
            min_length: int = 10,
            max_length: int = 200
    ):
        """
        Инициализация.

        Args:
            tech_keywords: Список технических ключевых слов для приоритизации
            min_length: Минимальная длина требования
            max_length: Максимальная длина требования
        """
        super().__init__(min_length, max_length)
        self.tech_keywords = [kw.lower() for kw in tech_keywords]

    def extract(self, text: str) -> List[str]:
        """
        Извлечение с приоритетом технических требований.

        Сначала возвращаются требования с техническими терминами,
        затем остальные.
        """
        # Базовое извлечение через родительский класс
        base_requirements = super().extract(text)

        # Разделение на технические и общие требования
        tech_requirements = []
        other_requirements = []

        for req in base_requirements:
            req_lower = req.lower()

            # Проверка наличия технических терминов
            has_tech = any(kw in req_lower for kw in self.tech_keywords)

            if has_tech:
                tech_requirements.append(req)
            else:
                other_requirements.append(req)

        # Технические требования в приоритете
        return tech_requirements + other_requirements

    def get_tech_requirements_only(self, text: str) -> List[str]:
        """
        Получение только технических требований.

        Args:
            text: Текст для анализа

        Returns:
            Список только технических требований
        """
        all_requirements = super().extract(text)

        tech_requirements = []

        for req in all_requirements:
            req_lower = req.lower()

            if any(kw in req_lower for kw in self.tech_keywords):
                tech_requirements.append(req)

        return tech_requirements
