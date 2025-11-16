# Рефакторинг проекта по принципам ООП и SOLID

## Структура проекта

```
project/
├── core/
│   ├── __init__.py
│   └── interfaces.py
├── fetchers/
│   ├── __init__.py
│   ├── searcher.py
│   └── details_fetcher.py
├── storage/
│   ├── __init__.py
│   └── savers.py
├── analytics/
│   ├── __init__.py
│   └── analyzer.py
├── visualization/
│   ├── __init__.py
│   └── visualizer.py
├── pipeline/
│   ├── __init__.py
│   └── vacancy_pipeline.py
├── config.py
└── main.py
```

---


## Как это соответствует SOLID:

1. **Single Responsibility (S)**: Каждый класс имеет одну ответственность:
   - `VacancySearcher` - только поиск
   - `DetailsFetcher` - только получение деталей
   - `Saver` - только сохранение
   - `Analyzer` - только анализ
   - `Visualizer` - только визуализация

2. **Open/Closed (O)**: Система открыта для расширения:
   - Можно добавить новые форматы сохранения (XmlSaver, ExcelSaver)
   - Можно добавить новые источники данных
   - Не нужно менять существующий код

3. **Liskov Substitution (L)**: Все реализации взаимозаменяемы:
   - `SyncSearcher` и `AsyncSearcher` реализуют `IVacancySearcher`
   - Можно подставить любую реализацию

4. **Interface Segregation (I)**: Интерфейсы специализированы:
   - Отдельные интерфейсы для поиска, получения деталей, сохранения, анализа

5. **Dependency Inversion (D)**: Зависимость от абстракций:
   - `VacancyPipeline` зависит от интерфейсов, а не от конкретных классов
   - Dependency Injection через конструктор

## Преимущества новой архитектуры:

✅ Легко тестировать (можно создать mock-объекты)  
✅ Легко расширять (новые форматы, источники данных)  
✅ Переиспользуемые компоненты  
✅ Четкое разделение ответственности  
✅ Гибкая конфигурация через DI  