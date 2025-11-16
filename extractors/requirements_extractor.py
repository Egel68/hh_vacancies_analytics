"""
Модуль извлечения требований к кандидату из текста описания.
Улучшенная версия с фильтрацией шума и умной дедупликацией.
"""

import re
from typing import List, Set, Dict
from difflib import SequenceMatcher
from core.interfaces import ITextSectionExtractor


class RequirementsExtractor(ITextSectionExtractor):
    """Извлечение требований к кандидату из текста вакансии."""

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
        r'наш идеальный кандидат:?',
        r'вы нам подходите:?',
        r'технические требования:?',
        r'hard skills:?',
        r'кого ищем:?',
        r'наши ожидания:?',
        r'от кандидата:?',
    ]

    # Паттерны-маркеры требований
    REQUIREMENT_MARKERS = [
        r'опыт работы',
        r'опыт.*?(?:от|не менее|более)',
        r'знание',
        r'знания',
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
        r'умеет',
        r'знает',
        r'имеет опыт',
        r'понимает',
    ]

    # НОВОЕ: Стоп-паттерны для исключения нерелевантных секций
    STOP_SECTION_HEADERS = [
        r'(?:что )?мы предлагаем:?',
        r'условия работы?:?',
        r'условия:?',
        r'we offer:?',
        r'benefits:?',
        r'о компании:?',
        r'о нас:?',
        r'about (?:us|company):?',
        r'зарплата:?',
        r'salary:?',
        r'compensation:?',
        r'бенефиты:?',
        r'корпоративная жизнь:?',
        r'оформление:?',
        r'график работы:?',
        r'локация:?',
        r'location:?',
        r'офис:?',
        r'формат работы:?',
        r'соц\.?\s*пакет:?',
        r'развитие:?',
        r'обучение:?',
    ]

    # НОВОЕ: Стоп-слова/фразы внутри требований
    NOISE_PHRASES = [
        r'^мы предлагаем',
        r'^что мы предлагаем',
        r'^условия',
        r'^оформление',
        r'^работа в офисе',
        r'^удал[её]нн?ый формат',
        r'^гибридный формат',
        r'^график',
        r'^зарплата',
        r'^з/?п',
        r'^\d+/\d+',  # 5/2
        r'^офис',
        r'^локация',
        r'^дмс',
        r'^вмс',
        r'корпоратив',
        r'тимбилдинг',
        r'бесплатн[ыо][йе]',
        r'компенсаци[яю]',
    ]

    def __init__(
            self,
            min_length: int = 15,
            max_length: int = 300,
            min_words: int = 3,
            similarity_threshold: float = 0.85
    ):
        """
        Инициализация экстрактора.

        Args:
            min_length: Минимальная длина требования (символов)
            max_length: Максимальная длина требования (символов)
            min_words: Минимальное количество слов
            similarity_threshold: Порог схожести для дедупликации (0-1)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_words = min_words
        self.similarity_threshold = similarity_threshold
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция регулярных выражений."""
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(?:' + '|'.join(self.REQUIREMENT_HEADERS) + r')\s*(?:\n|$)',
            re.IGNORECASE | re.MULTILINE
        )
        self.marker_pattern = re.compile(
            r'\b(?:' + '|'.join(self.REQUIREMENT_MARKERS) + r')',
            re.IGNORECASE
        )
        self.stop_section_pattern = re.compile(
            r'(?:^|\n)\s*(?:' + '|'.join(self.STOP_SECTION_HEADERS) + r')',
            re.IGNORECASE | re.MULTILINE
        )
        self.noise_pattern = re.compile(
            '|'.join(self.NOISE_PHRASES),
            re.IGNORECASE
        )

    def extract(self, text: str) -> List[str]:
        """Извлечение требований из текста."""
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

        # УЛУЧШЕННАЯ очистка и дедупликация
        requirements = self._advanced_clean_and_deduplicate(requirements)

        return requirements

    def _extract_from_sections(self, text: str) -> List[str]:
        """Извлечение требований из размеченных секций."""
        requirements = []

        # Поиск всех секций с требованиями
        for match in self.header_pattern.finditer(text):
            section_start = match.end()

            # Поиск конца секции
            section_end = self._find_section_end(text, section_start)

            if section_end is None:
                section_end = len(text)

            section_text = text[section_start:section_end]

            # Проверка, что это не стоп-секция
            if not self.stop_section_pattern.search(match.group()):
                items = self._split_into_items(section_text)
                requirements.extend(items)

        return requirements

    def _find_section_end(self, text: str, start_pos: int) -> int:
        """Поиск конца текущей секции."""
        # Ищем следующий заголовок (любой)
        next_headers_pattern = re.compile(
            r'\n\s*(?:'
            r'обязанности|'
            r'задачи|'
            r'responsibilities|'
            r'условия|'
            r'мы предлагаем|'
            r'what we offer|'
            r'benefits|'
            r'о компании|'
            r'требования|'
            r'requirements'
            r'):',
            re.IGNORECASE
        )

        match = next_headers_pattern.search(text[start_pos:])

        if match:
            return start_pos + match.start()

        return len(text)

    def _extract_by_markers(self, text: str) -> List[str]:
        """Извлечение требований по ключевым маркерам."""
        requirements = []

        # Разбиение на предложения
        sentences = re.split(r'[.!?]\s+', text)

        for sentence in sentences:
            # Проверка наличия маркеров
            if self.marker_pattern.search(sentence):
                cleaned = sentence.strip()

                # Фильтрация
                if self._is_valid_requirement(cleaned):
                    requirements.append(cleaned)

        return requirements

    def _extract_from_lists(self, text: str) -> List[str]:
        """Извлечение из маркированных и нумерованных списков."""
        requirements = []

        list_patterns = [
            r'^[-•*]\s*(.+)$',
            r'^\d+[\.)]\s*(.+)$',
        ]

        lines = text.split('\n')

        for line in lines:
            for pattern in list_patterns:
                match = re.match(pattern, line.strip())

                if match:
                    item = match.group(1).strip()

                    if self._is_valid_requirement(item):
                        requirements.append(item)
                    break

        return requirements

    def _split_into_items(self, text: str) -> List[str]:
        """Разбиение текста на отдельные элементы."""
        items = []

        # Разбиение по разделителям
        separators = [';', '\n']
        current_items = [text]

        for sep in separators:
            new_items = []
            for item in current_items:
                new_items.extend(item.split(sep))
            current_items = new_items

        # Разбиение по точке (если после точки заглавная буква)
        final_items = []
        for item in current_items:
            parts = re.split(r'\.\s+(?=[А-ЯA-ZЁ])', item)
            final_items.extend(parts)

        # Фильтрация и очистка
        for item in final_items:
            cleaned = self._clean_item(item)

            if self._is_valid_requirement(cleaned):
                items.append(cleaned)

        return items

    def _clean_item(self, text: str) -> str:
        """Очистка отдельного элемента."""
        # Удаление начальных маркеров
        text = re.sub(r'^[-•*\d+\.)]\s*', '', text)

        # Удаление лишних пробелов
        text = ' '.join(text.split())

        return text.strip()

    def _is_valid_requirement(self, text: str) -> bool:
        """Проверка валидности требования."""
        if not text:
            return False

        # Проверка длины
        if len(text) < self.min_length or len(text) > self.max_length:
            return False

        # Проверка количества слов
        words = text.split()
        if len(words) < self.min_words:
            return False

        # Исключение заголовков (заканчиваются на ":")
        if text.strip().endswith(':'):
            return False

        # Исключение стоп-фраз
        if self.noise_pattern.search(text):
            return False

        # Исключение чисто числовых значений
        if re.match(r'^\d+[\s\-/]*\d*$', text.strip()):
            return False

        return True

    def _advanced_clean_and_deduplicate(self, requirements: List[str]) -> List[str]:
        """
        Продвинутая очистка и дедупликация.

        Использует нечеткое сравнение для удаления похожих элементов.
        """
        if not requirements:
            return []

        # Предварительная очистка
        cleaned = [req for req in requirements if self._is_valid_requirement(req)]

        # Нечеткая дедупликация
        unique_requirements = []

        for req in cleaned:
            is_duplicate = False

            # Сравнение с уже добавленными
            for existing in unique_requirements:
                similarity = self._calculate_similarity(req, existing)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_requirements.append(req)

        return unique_requirements

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести двух строк (0-1)."""
        # Нормализация для сравнения
        norm1 = ' '.join(text1.lower().split())
        norm2 = ' '.join(text2.lower().split())

        return SequenceMatcher(None, norm1, norm2).ratio()


class SkillsBasedRequirementsExtractor(RequirementsExtractor):
    """Расширенный экстрактор с фокусом на технические навыки."""

    def __init__(
            self,
            tech_keywords: List[str],
            min_length: int = 15,
            max_length: int = 300,
            min_words: int = 3,
            similarity_threshold: float = 0.85
    ):
        super().__init__(min_length, max_length, min_words, similarity_threshold)
        self.tech_keywords = [kw.lower() for kw in tech_keywords]

    def extract(self, text: str) -> List[str]:
        """Извлечение с приоритетом технических требований."""
        base_requirements = super().extract(text)

        # Разделение на технические и общие
        tech_requirements = []
        other_requirements = []

        for req in base_requirements:
            req_lower = req.lower()

            if any(kw in req_lower for kw in self.tech_keywords):
                tech_requirements.append(req)
            else:
                other_requirements.append(req)

        return tech_requirements + other_requirements

    def get_tech_requirements_only(self, text: str) -> List[str]:
        """Получение только технических требований."""
        all_requirements = super().extract(text)

        return [
            req for req in all_requirements
            if any(kw in req.lower() for kw in self.tech_keywords)
        ]
