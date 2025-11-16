"""
Модуль извлечения требований к кандидату из текста описания.
УЛУЧШЕННАЯ ВЕРСИЯ с расширенной фильтрацией шума.
"""

import re
from typing import List
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
        r'для нас важно:?',
        r'что ждем:?',
    ]

    # Паттерны-маркеры требований
    REQUIREMENT_MARKERS = [
        r'опыт работы',
        r'опыт.*?(?:от|не менее|более|\d+)',
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
        r'образование',
        r'высшее',
        r'уверенное',
        r'глубокое',
    ]

    # РАСШИРЕННЫЕ стоп-секции
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
        r'наши преимущества:?',
        r'почему мы:?',
        r'присоединяйтесь:?',
    ]

    # РАСШИРЕННЫЕ стоп-фразы
    NOISE_PHRASES = [
        # Что предлагает компания
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

        # О компании
        r'^о компании',
        r'^наша компания',
        r'^наша цель',
        r'^мы (?:являемся|занимаемся|создаем)',

        # Призывы
        r'^если вы хотите',
        r'^если (?:тебе|вам) важно',
        r'^будем рады',
        r'^ждем',
        r'^присоединяйтесь',

        # Маркетинг и преимущества
        r'^уникальн',
        r'^отличн',
        r'^прекрасн',
        r'^профессиональный рост',
        r'^карьерный рост',
        r'^возможность (?:развития|роста)',
        r'^перспективы',
        r'^конкурентн[аы][яй] зарплат',
        r'^комфортн[аы][яй]',
        r'^дружн[аы][яй] команд',

        # Эмодзи
        r'📩|📧|✉️|💼|🎯|🚀|⭐|✨|🔍|📊|📈|💰|🏆',
    ]

    def __init__(
            self,
            min_length: int = 15,
            max_length: int = 300,
            min_words: int = 3,
            similarity_threshold: float = 0.85
    ):
        """Инициализация экстрактора."""
        self.min_length = min_length
        self.max_length = max_length
        self.min_words = min_words
        self.similarity_threshold = similarity_threshold
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция регулярных выражений."""
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(?:' + '|'.join(self.REQUIREMENT_HEADERS) + r')\s*(?:\n|$)',
            re.IGNORECASE | re.MULTILINE | re.UNICODE
        )
        self.marker_pattern = re.compile(
            r'\b(?:' + '|'.join(self.REQUIREMENT_MARKERS) + r')',
            re.IGNORECASE | re.UNICODE
        )
        self.stop_section_pattern = re.compile(
            r'(?:^|\n)\s*(?:' + '|'.join(self.STOP_SECTION_HEADERS) + r')',
            re.IGNORECASE | re.MULTILINE | re.UNICODE
        )
        self.noise_pattern = re.compile(
            '|'.join(self.NOISE_PHRASES),
            re.IGNORECASE | re.UNICODE
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

        # Улучшенная очистка и дедупликация
        requirements = self._advanced_clean_and_deduplicate(requirements)

        return requirements

    def _extract_from_sections(self, text: str) -> List[str]:
        """Извлечение требований из размеченных секций."""
        requirements = []

        for match in self.header_pattern.finditer(text):
            section_start = match.end()
            section_end = self._find_section_end(text, section_start)

            if section_end is None:
                section_end = len(text)

            section_text = text[section_start:section_end]

            if not self.stop_section_pattern.search(match.group()):
                items = self._split_into_items(section_text)
                requirements.extend(items)

        return requirements

    def _find_section_end(self, text: str, start_pos: int) -> int:
        """Поиск конца текущей секции."""
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
            re.IGNORECASE | re.UNICODE
        )

        match = next_headers_pattern.search(text[start_pos:])

        if match:
            return start_pos + match.start()

        return len(text)

    def _extract_by_markers(self, text: str) -> List[str]:
        """Извлечение требований по ключевым маркерам."""
        requirements = []
        sentences = re.split(r'[.!?]\s+', text)

        for sentence in sentences:
            if self.marker_pattern.search(sentence):
                cleaned = sentence.strip()

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

        separators = [';', '\n']
        current_items = [text]

        for sep in separators:
            new_items = []
            for item in current_items:
                new_items.extend(item.split(sep))
            current_items = new_items

        # Разбиение по точке
        final_items = []
        for item in current_items:
            parts = re.split(r'\.\s+(?=[А-ЯA-ZЁ])', item)
            final_items.extend(parts)

        for item in final_items:
            cleaned = self._clean_item(item)

            if self._is_valid_requirement(cleaned):
                items.append(cleaned)

        return items

    def _clean_item(self, text: str) -> str:
        """Очистка отдельного элемента."""
        # Удаление эмодзи
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)

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

        # Исключение заголовков
        if text.strip().endswith(':'):
            return False

        # Исключение стоп-фраз
        if self.noise_pattern.search(text):
            return False

        # Исключение чисто числовых значений
        if re.match(r'^\d+[\s\-/]*\d*$', text.strip()):
            return False

        # Исключение слишком общих фраз
        generic_phrases = [
            'мы рассматриваем кандидатов',
            'идеальный кандидат',
            'вы нам подходите',
        ]

        text_lower = text.lower()
        for phrase in generic_phrases:
            if phrase in text_lower and len(text) < 100:
                return False

        return True

    def _advanced_clean_and_deduplicate(self, requirements: List[str]) -> List[str]:
        """Продвинутая очистка и дедупликация."""
        if not requirements:
            return []

        cleaned = [req for req in requirements if self._is_valid_requirement(req)]

        unique_requirements = []

        for req in cleaned:
            is_duplicate = False

            for existing in unique_requirements:
                similarity = self._calculate_similarity(req, existing)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_requirements.append(req)

        return unique_requirements

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести двух строк."""
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
