"""
Модуль извлечения обязанностей и задач из описания вакансии.
УЛУЧШЕННАЯ ВЕРСИЯ с расширенной фильтрацией шума.
"""

import re
from typing import List
from difflib import SequenceMatcher
from core.interfaces import ITextSectionExtractor


class ResponsibilitiesExtractor(ITextSectionExtractor):
    """Извлечение обязанностей и задач из текста вакансии."""

    # Паттерны заголовков секций с обязанностями
    RESPONSIBILITY_HEADERS = [
        r'обязанности:',
        r'ваши обязанности:',
        r'в ваши обязанности входит:',
        r'задачи:',
        r'ваши задачи:',
        r'вам предстоит:',
        r'чем предстоит заниматься:',
        r'responsibilities:',
        r'duties:',
        r'what you.*?ll do:',
        r'you will:',
        r'your responsibilities:',
        r'в работе:',
        r'что нужно делать:',
        r'функционал:',
        r'основные задачи:',
        r'чем заниматься:',
        r'чем предстоит:',
        r'примеры задач:',
        r'что предстоит делать:',
        r'какие задачи:',
    ]

    # Паттерны-маркеры задач
    TASK_MARKERS = [
        r'\b(?:разработка|разработать|develop)',
        r'\b(?:проектирование|проектировать|design)',
        r'\b(?:внедрение|внедрить|implement)',
        r'\b(?:поддержка|поддерживать|maintain)',
        r'\b(?:оптимизация|оптимизировать|optimize)',
        r'\b(?:участие в|participation)',
        r'\b(?:работа с|working with)',
        r'\b(?:взаимодействие|collaborate)',
        r'\b(?:создание|создавать|create)',
        r'\b(?:анализ|анализировать|analyze)',
        r'\b(?:сбор|собирать|collect)',
        r'\b(?:формирование|формировать)',
        r'\b(?:тестирование|тестировать)',
        r'\b(?:настройка|настраивать)',
        r'\b(?:интеграция|интегрировать)',
        r'\b(?:обеспечить|обеспечивать)',
        r'\b(?:описание|описывать)',
        r'\b(?:автоматизация|автоматизировать)',
        r'\b(?:контроль|контролировать)',
        r'\b(?:ведение|вести)',
        r'\b(?:подготовка|подготовить)',
        r'\b(?:построение|построить)',
        r'\b(?:поиск|искать)',
    ]

    # РАСШИРЕННЫЕ стоп-секции
    STOP_SECTION_HEADERS = [
        r'(?:что )?мы предлагаем:?',
        r'условия работы?:?',
        r'условия:?',
        r'we offer:?',
        r'benefits:?',
        r'о компании:?',
        r'требования:?',
        r'requirements:?',
        r'зарплата:?',
        r'бенефиты:?',
        r'корпоративная жизнь:?',
        r'график работы:?',
        r'формат работы:?',
        r'наши преимущества:?',
        r'почему мы:?',
        r'нам важно:?',
        r'от кандидата:?',
    ]

    # РАСШИРЕННЫЕ стоп-фразы
    NOISE_PHRASES = [
        # Информация о компании
        r'^за\s+\d+\s+(?:лет|года|год)',
        r'^мы помогли',
        r'помогли\s+\d+\+?\s*компани',
        r'внедрить\s+системное\s+управление',
        r'повысить\s+эффективность',
        r'сократить\s+затраты',

        # Что предлагает компания
        r'^мы предлагаем',
        r'^что мы предлагаем',
        r'^условия',
        r'^оформление',
        r'^удал[её]нн?ый формат',
        r'^гибридный формат',
        r'^график',
        r'^зарплата',
        r'^\d+/\d+',
        r'^офис',
        r'^дмс',
        r'корпоратив',
        r'тимбилдинг',

        # О компании и маркетинг
        r'^наша цель',
        r'^мы (?:являемся|занимаемся|создаем)',
        r'^компания (?:специализируется|работает)',
        r'^если вы хотите',
        r'^будем рады',
        r'^ждем (?:вас|тебя)',
        r'^присоединяйтесь',

        # Преимущества и бенефиты
        r'^уникальн[аы][яй] экспертиз',
        r'^профессиональный рост',
        r'^карьерный рост',
        r'^возможность (?:развития|роста|обучения)',
        r'^наставничество',
        r'^обучение (?:внутри|за счет)',
        r'^конкурентн[аы][яй] зарплат',
        r'^комфортн[аы][яй]',
        r'^гибкий график',
        r'^удаленн[аы][яй] работ',
        r'^максимальное влияние',
        r'^работа в постоянно развивающейся',

        # Общие фразы
        r'^отличн',
        r'^прекрасн',
        r'^индивидуальная программа',
        r'^бонусы',
        r'^компенсация',
        r'^стабильная',
        r'^адекватное',

        # Требования, попавшие в обязанности
        r'^опыт работы',
        r'^знание',
        r'^владение',
        r'^умение.*?(?:работать с|использовать)',
        r'^понимание.*?(?:принципов|основ)',
        r'^навык[ии]?\s+(?:работы с|использования)',
        r'^высшее образование',
        r'^образование',
        r'^уверенное',
        r'^глубокое',
        r'^техническая насмотренность',
        r'^базовые основы',
        r'^понимание основ',

        # Эмодзи
        r'📩|📧|✉️|💼|🎯|🚀|⭐|✨|🔍|📊|📈|💰|🏆',
    ]

    def __init__(
            self,
            min_length: int = 20,
            max_length: int = 450,
            min_words: int = 4,
            similarity_threshold: float = 0.85
    ):
        """Инициализация экстрактора обязанностей."""
        self.min_length = min_length
        self.max_length = max_length
        self.min_words = min_words
        self.similarity_threshold = similarity_threshold
        self._compile_patterns()

    def _compile_patterns(self):
        """Компиляция регулярных выражений."""
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(?:' + '|'.join(self.RESPONSIBILITY_HEADERS) + r')\s*(?:\n|$)',
            re.IGNORECASE | re.MULTILINE | re.UNICODE
        )
        self.marker_pattern = re.compile(
            r'(?:' + '|'.join(self.TASK_MARKERS) + r')',
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
        """Извлечение обязанностей из текста."""
        if not text:
            return []

        responsibilities = []

        section_resp = self._extract_from_sections(text)
        responsibilities.extend(section_resp)

        marker_resp = self._extract_by_markers(text)
        responsibilities.extend(marker_resp)

        list_resp = self._extract_from_lists(text)
        responsibilities.extend(list_resp)

        responsibilities = self._advanced_clean_and_deduplicate(responsibilities)

        return responsibilities

    def _extract_from_sections(self, text: str) -> List[str]:
        """Извлечение из секций."""
        responsibilities = []

        for match in self.header_pattern.finditer(text):
            section_start = match.end()
            section_end = self._find_section_end(text, section_start)

            if section_end is None:
                section_end = len(text)

            section_text = text[section_start:section_end]

            if not self.stop_section_pattern.search(match.group()):
                items = self._split_into_items(section_text)
                responsibilities.extend(items)

        return responsibilities

    def _find_section_end(self, text: str, start_pos: int) -> int:
        """Поиск конца секции."""
        next_headers_pattern = re.compile(
            r'\n\s*(?:'
            r'требования|'
            r'условия|'
            r'мы предлагаем|'
            r'what we offer|'
            r'requirements|'
            r'о компании|'
            r'обязанности|'
            r'задачи|'
            r'нам важно|'
            r'от кандидата'
            r'):',
            re.IGNORECASE | re.UNICODE
        )

        match = next_headers_pattern.search(text[start_pos:])

        if match:
            return start_pos + match.start()

        return len(text)

    def _extract_by_markers(self, text: str) -> List[str]:
        """Извлечение по маркерам."""
        responsibilities = []
        sentences = re.split(r'[.;!?]\s+', text)

        for sentence in sentences:
            if self.marker_pattern.search(sentence):
                cleaned = sentence.strip()

                if self._is_valid_responsibility(cleaned):
                    responsibilities.append(cleaned)

        return responsibilities

    def _extract_from_lists(self, text: str) -> List[str]:
        """Извлечение из списков."""
        responsibilities = []

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

                    if self._is_valid_responsibility(item):
                        responsibilities.append(item)
                    break

        return responsibilities

    def _split_into_items(self, text: str) -> List[str]:
        """Разбиение на элементы."""
        items = []

        separators = [';', '\n']
        current_items = [text]

        for sep in separators:
            new_items = []
            for item in current_items:
                new_items.extend(item.split(sep))
            current_items = new_items

        final_items = []
        for item in current_items:
            parts = re.split(r'\.\s+(?=[А-ЯA-ZЁ])', item)
            final_items.extend(parts)

        for item in final_items:
            cleaned = self._clean_item(item)

            if self._is_valid_responsibility(cleaned):
                items.append(cleaned)

        return items

    def _clean_item(self, text: str) -> str:
        """Очистка элемента."""
        # Удаление эмодзи
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)

        # Удаление маркеров списков
        text = re.sub(r'^[-•*\d+\.)]\s*', '', text)

        # Нормализация пробелов
        text = ' '.join(text.split())

        # Удаление точки с запятой в конце
        text = text.rstrip(';').rstrip('.')

        return text.strip()

    def _is_valid_responsibility(self, text: str) -> bool:
        """Проверка валидности обязанности."""
        if not text:
            return False

        if len(text) < self.min_length or len(text) > self.max_length:
            return False

        words = text.split()
        if len(words) < self.min_words:
            return False

        if text.strip().endswith(':'):
            return False

        if self.noise_pattern.search(text):
            return False

        if re.match(r'^\d+[\s\-/]*\d*$', text.strip()):
            return False

        # Дополнительная проверка: исключение требований
        requirement_patterns = [
            r'^опыт\s+работы',
            r'^опыт\s+от',
            r'^знание\s+',
            r'^владение\s+',
            r'^умение\s+работать\s+с\s+',
            r'^навык[ии]?\s+',
            r'^понимание\s+принципов',
            r'^понимание\s+основ',
            r'^высшее\s+образование',
            r'^образование',
            r'^техническая\s+насмотренность',
            r'^базовые\s+основы',
            r'^уверенн[оы][ей]\s+(?:владение|знание)',
        ]

        text_lower = text.lower()
        for pattern in requirement_patterns:
            if re.search(pattern, text_lower):
                return False

        return True

    def _advanced_clean_and_deduplicate(self, responsibilities: List[str]) -> List[str]:
        """Продвинутая дедупликация."""
        if not responsibilities:
            return []

        cleaned = [r for r in responsibilities if self._is_valid_responsibility(r)]

        unique_resp = []
        seen_normalized = set()

        for resp in cleaned:
            # Нормализация для сравнения
            normalized = self._normalize_for_comparison(resp)

            if normalized in seen_normalized:
                continue

            is_duplicate = False

            for existing in unique_resp:
                similarity = self._calculate_similarity(resp, existing)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_resp.append(resp)
                seen_normalized.add(normalized)

        return unique_resp

    def _normalize_for_comparison(self, text: str) -> str:
        """Нормализация текста для сравнения."""
        # Приведение к нижнему регистру
        text = text.lower()

        # Удаление знаков препинания в конце
        text = text.rstrip('.;,')

        # Нормализация пробелов
        text = ' '.join(text.split())

        return text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести."""
        norm1 = self._normalize_for_comparison(text1)
        norm2 = self._normalize_for_comparison(text2)

        return SequenceMatcher(None, norm1, norm2).ratio()
