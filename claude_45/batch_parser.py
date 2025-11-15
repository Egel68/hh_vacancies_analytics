import asyncio
from typing import List, Dict
import json
from hh_parser_async import HHParserAsync
from processing import VacancyAnalyzer
import pandas as pd


async def parse_multiple_queries(queries: List[str], area: int = 1,
                                 max_vacancies_per_query: int = 100) -> Dict[str, List[Dict]]:
    """
    Асинхронный парсинг нескольких должностей одновременно
    """
    parser = HHParserAsync(max_concurrent_requests=15)

    tasks = []
    for query in queries:
        task = parser.parse_vacancies(query, area, max_vacancies_per_query)
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    return {query: result for query, result in zip(queries, results)}


def batch_analysis(queries: List[str], area: int = 1, max_vacancies: int = 100):
    """
    Пакетный анализ нескольких должностей
    """
    print("=" * 60)
    print("ПАКЕТНЫЙ АНАЛИЗ ВАКАНСИЙ")
    print("=" * 60)
    print(f"Должности для анализа: {', '.join(queries)}\n")

    # Асинхронный парсинг
    loop = asyncio.get_event_loop()
    all_results = loop.run_until_complete(
        parse_multiple_queries(queries, area, max_vacancies)
    )

    # Анализ каждой должности
    summary = []

    for query, vacancies in all_results.items():
        print(f"\n{'=' * 60}")
        print(f"Анализ: {query}")
        print(f"{'=' * 60}")

        if not vacancies:
            print(f"❌ Вакансии не найдены для: {query}")
            continue

        # Сохранение данных
        filename = query.replace(' ', '_').lower()
        with open(f'{filename}_raw.json', 'w', encoding='utf-8') as f:
            json.dump(vacancies, f, ensure_ascii=False, indent=2)

        # Анализ
        analyzer = VacancyAnalyzer(vacancies)
        df = analyzer.extract_data()
        df.to_csv(f'{filename}_processed.csv', index=False, encoding='utf-8-sig')

        skills_df = analyzer.analyze_skills()
        skills_df.to_csv(f'{filename}_skills.csv', index=False, encoding='utf-8-sig')

        # Сводка
        top_skills = skills_df.head(5)['Навык'].tolist()
        salary_stats = analyzer.get_salary_stats()

        summary_item = {
            'Должность': query,
            'Вакансий': len(df),
            'Топ-5 навыков': ', '.join(top_skills),
            'Средняя ЗП (от)': salary_stats.get('avg_from', 'N/A'),
            'Медиана ЗП (от)': salary_stats.get('median_from', 'N/A')
        }
        summary.append(summary_item)

        print(f"✅ Обработано вакансий: {len(df)}")
        print(f"📌 Топ-5 навыков: {', '.join(top_skills)}")

    # Общая сводка
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('batch_summary.csv', index=False, encoding='utf-8-sig')

    print("\n" + "=" * 60)
    print("ОБЩАЯ СВОДКА")
    print("=" * 60)
    print(summary_df.to_string(index=False))
    print("\n✅ Пакетный анализ завершен!")


if __name__ == "__main__":
    # Пример использования
    queries = [
        'Python разработчик',
        'Data Scientist',
        'Machine Learning Engineer',
        'Backend разработчик'
    ]

    batch_analysis(queries, area=1, max_vacancies=100)