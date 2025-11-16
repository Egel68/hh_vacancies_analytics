"""
Модуль пакетного анализа вакансий с hh.ru.

Поддерживает синхронный и асинхронный режимы обработки
множественных должностей одновременно.
"""

import asyncio
import json
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from getData import parse_vacancies_sync
from processing import VacancyAnalyzer
from visualization import visualize_results


def analyze_single_query(
        query: str,
        vacancies: List[Dict],
        base_output_dir: str = "./result"
) -> Dict:
    """
    Выполняет анализ вакансий для одной должности.

    Args:
        query: Название должности для поиска
        vacancies: Список словарей с данными вакансий
        base_output_dir: Базовая директория для сохранения результатов

    Returns:
        Словарь со статистикой анализа, включающий:
            - Должность
            - Количество вакансий
            - Топ-5 навыков
            - Статистику по зарплатам
            - Путь к папке с результатами
    """
    safe_query = query.replace(' ', '_').replace('/', '_').lower()
    output_dir = Path(base_output_dir) / safe_query
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"📊 Анализ: {query}")
    print(f"{'=' * 60}")

    if not vacancies:
        print(f"❌ Вакансии не найдены для: {query}")
        return {}

    # Сохранение сырых данных
    with open(output_dir / 'raw.json', 'w', encoding='utf-8') as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено: raw.json")

    # Анализ данных
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение обработанных данных
    df.to_csv(output_dir / 'processed.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: processed.csv ({len(df)} вакансий)")

    # Анализ навыков
    skills_df = analyzer.analyze_skills()
    skills_df.to_csv(output_dir / 'skills.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: skills.csv")

    # Анализ требований
    requirements_df = analyzer.analyze_requirements()
    requirements_df.to_csv(output_dir / 'requirements.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: requirements.csv")

    # Статистика по зарплатам
    salary_stats = analyzer.get_salary_stats()
    with open(output_dir / 'salary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(salary_stats, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено: salary_stats.json")

    # Визуализация
    print(f"\n📈 Создаем визуализации...")
    visualize_results(analyzer, output_dir=str(output_dir), prefix="", show_plots=False)

    # Формирование сводки
    top_skills = skills_df.head(5)['Навык'].tolist() if len(skills_df) > 0 else []

    summary = {
        'Должность': query,
        'Вакансий': len(df),
        'Топ-5 навыков': ', '.join(top_skills),
        'Средняя ЗП (от)': salary_stats.get('avg_from', 'N/A'),
        'Медиана ЗП (от)': salary_stats.get('median_from', 'N/A'),
        'Папка': str(output_dir)
    }

    print(f"\n✅ Анализ завершен для: {query}")
    print(f"📁 Результаты в папке: {output_dir}")

    return summary


def batch_analysis_sync(
    queries: List[str],
    area: int = 1,
    max_vacancies: int = 100,
    output_dir: str = "./result"
) -> None:
    """
    Выполняет пакетный синхронный анализ нескольких должностей.

    Args:
        queries: Список названий должностей для анализа
        area: Код региона поиска (1 - Москва, 2 - СПб, 113 - Россия)
        max_vacancies: Максимальное количество вакансий для анализа
        output_dir: Директория для сохранения результатов
    """
    print("=" * 60)
    print("🔄 ПАКЕТНЫЙ СИНХРОННЫЙ АНАЛИЗ ВАКАНСИЙ")
    print("=" * 60)
    print(f"Должности: {', '.join(queries)}\n")

    summary_list = []

    for query in queries:
        # Парсинг вакансий (БЕЗ сохранения raw файла)
        vacancies = parse_vacancies_sync(
            query=query,
            area=area,
            max_vacancies=max_vacancies,
            output_dir=output_dir,
            save_raw=False  # <- Отключаем сохранение в базовую папку
        )

        # Анализ данных (raw.json сохранится в правильную подпапку)
        summary = analyze_single_query(query, vacancies, output_dir)
        if summary:
            summary_list.append(summary)

    # Создание общей сводки
    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        summary_path = Path(output_dir) / 'batch_summary.csv'
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

        print("\n" + "=" * 60)
        print("📋 ОБЩАЯ СВОДКА")
        print("=" * 60)
        print(summary_df.to_string(index=False))
        print(f"\n💾 Сводка сохранена: {summary_path}")

    print("\n✅ Пакетный анализ завершен!")


async def batch_analysis_async(
    queries: List[str],
    area: int = 1,
    max_vacancies: int = 100,
    max_concurrent: int = 10,
    output_dir: str = "./result"
) -> None:
    """
    Выполняет пакетный асинхронный анализ нескольких должностей.

    Args:
        queries: Список названий должностей для анализа
        area: Код региона поиска (1 - Москва, 2 - СПб, 113 - Россия)
        max_vacancies: Максимальное количество вакансий для анализа
        max_concurrent: Максимальное количество одновременных запросов
        output_dir: Директория для сохранения результатов
    """
    print("=" * 60)
    print("⚡ ПАКЕТНЫЙ АСИНХРОННЫЙ АНАЛИЗ ВАКАНСИЙ")
    print("=" * 60)
    print(f"Должности: {', '.join(queries)}\n")

    from hh_parser_async import HHParserAsync

    parser = HHParserAsync(max_concurrent_requests=max_concurrent, output_dir=output_dir)

    # Параллельный парсинг всех должностей (raw файлы НЕ сохраняются автоматически)
    tasks = [parser.parse_vacancies(query, area, max_vacancies) for query in queries]
    results = await asyncio.gather(*tasks)
    all_results = dict(zip(queries, results))

    # Анализ каждой должности (raw.json сохранится в правильную подпапку)
    summary_list = []
    for query, vacancies in all_results.items():
        summary = analyze_single_query(query, vacancies, output_dir)
        if summary:
            summary_list.append(summary)

    # Создание общей сводки
    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        summary_path = Path(output_dir) / 'batch_summary.csv'
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

        print("\n" + "=" * 60)
        print("📋 ОБЩАЯ СВОДКА")
        print("=" * 60)
        print(summary_df.to_string(index=False))
        print(f"\n💾 Сводка сохранена: {summary_path}")

    print("\n✅ Пакетный анализ завершен!")


def run_batch_analysis(
        queries: List[str],
        area: int = 1,
        max_vacancies: int = 100,
        async_mode: bool = True,
        max_concurrent: int = 10,
        output_dir: str = "./result"
) -> None:
    """
    Запускает пакетный анализ в синхронном или асинхронном режиме.

    Args:
        queries: Список названий должностей для анализа
        area: Код региона поиска (1 - Москва, 2 - СПб, 113 - Россия)
        max_vacancies: Максимальное количество вакансий для анализа
        async_mode: Если True - асинхронный режим, иначе синхронный
        max_concurrent: Максимальное количество одновременных запросов (для async)
        output_dir: Директория для сохранения результатов
    """
    if async_mode:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            batch_analysis_async(queries, area, max_vacancies, max_concurrent, output_dir)
        )
    else:
        batch_analysis_sync(queries, area, max_vacancies, output_dir)


if __name__ == "__main__":
    queries = [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer'
    ]

    run_batch_analysis(
        queries=queries,
        area=1,
        max_vacancies=100,
        async_mode=True,
        max_concurrent=8,
        output_dir="./result"
    )
