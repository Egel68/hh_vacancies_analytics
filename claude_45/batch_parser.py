import asyncio
import json
from typing import List, Dict
from pathlib import Path
import pandas as pd

from getData import parse_vacancies_sync
from hh_parser_async import parse_vacancies_async
from processing import VacancyAnalyzer
from visualization import visualize_results


def analyze_single_query(query: str, vacancies: List[Dict],
                         base_output_dir: str = "./result") -> Dict:
    """
    Анализ одной должности

    Returns:
        Словарь со статистикой
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

    # Анализ
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение обработанных данных
    df.to_csv(output_dir / 'processed.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: processed.csv ({len(df)} вакансий)")

    # Навыки
    skills_df = analyzer.analyze_skills()
    skills_df.to_csv(output_dir / 'skills.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: skills.csv")

    # Требования
    requirements_df = analyzer.analyze_requirements()
    requirements_df.to_csv(output_dir / 'requirements.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Сохранено: requirements.csv")

    # Зарплаты
    salary_stats = analyzer.get_salary_stats()
    with open(output_dir / 'salary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(salary_stats, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено: salary_stats.json")

    # Визуализация
    print(f"\n📈 Создаем визуализации...")
    visualize_results(analyzer, output_dir=str(output_dir), prefix="", show_plots=False)

    # Формируем сводку
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


def batch_analysis_sync(queries: List[str], area: int = 1,
                        max_vacancies: int = 100,
                        output_dir: str = "./result"):
    """
    Пакетный СИНХРОННЫЙ анализ нескольких должностей
    """
    print("=" * 60)
    print("🔄 ПАКЕТНЫЙ СИНХРОННЫЙ АНАЛИЗ ВАКАНСИЙ")
    print("=" * 60)
    print(f"Должности: {', '.join(queries)}\n")

    summary_list = []

    for query in queries:
        # Парсинг
        vacancies = parse_vacancies_sync(
            query=query,
            area=area,
            max_vacancies=max_vacancies,
            output_dir=output_dir
        )

        # Анализ
        summary = analyze_single_query(query, vacancies, output_dir)
        if summary:
            summary_list.append(summary)

    # Общая сводка
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


async def batch_analysis_async(queries: List[str], area: int = 1,
                               max_vacancies: int = 100,
                               max_concurrent: int = 10,
                               output_dir: str = "./result"):
    """
    Пакетный АСИНХРОННЫЙ анализ нескольких должностей
    """
    print("=" * 60)
    print("⚡ ПАКЕТНЫЙ АСИНХРОННЫЙ АНАЛИЗ ВАКАНСИЙ")
    print("=" * 60)
    print(f"Должности: {', '.join(queries)}\n")

    # Импортируем парсер
    from hh_parser_async import HHParserAsync

    parser = HHParserAsync(max_concurrent_requests=max_concurrent, output_dir=output_dir)

    # Парсим все должности параллельно
    tasks = []
    for query in queries:
        task = parser.parse_vacancies(query, area, max_vacancies)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    all_results = {query: result for query, result in zip(queries, results)}

    # Анализируем каждую должность
    summary_list = []

    for query, vacancies in all_results.items():
        summary = analyze_single_query(query, vacancies, output_dir)
        if summary:
            summary_list.append(summary)

    # Общая сводка
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


def run_batch_analysis(queries: List[str], area: int = 1,
                       max_vacancies: int = 100,
                       async_mode: bool = True,
                       max_concurrent: int = 10,
                       output_dir: str = "./result"):
    """
    Запуск пакетного анализа (синхронно или асинхронно)
    """
    if async_mode:
        # Асинхронный режим
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
        # Синхронный режим
        batch_analysis_sync(queries, area, max_vacancies, output_dir)


if __name__ == "__main__":
    # Пример использования
    queries = [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer'
    ]

    run_batch_analysis(
        queries=queries,
        area=1,
        max_vacancies=100,
        async_mode=True,  # True - асинхронно, False - синхронно
        max_concurrent=8,
        output_dir="./result"
    )
