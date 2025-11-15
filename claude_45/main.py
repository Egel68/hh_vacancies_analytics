import json
from hh_parser_async import parse_vacancies_async
from processing import VacancyAnalyzer
from visualization import visualize_results


def main():
    """Основная функция с асинхронным парсером"""

    # Параметры парсинга
    config = {
        'query': 'Python разработчик',
        'area': 1,  # Москва
        'max_vacancies': 200,
        'max_concurrent': 15  # Количество одновременных запросов
    }

    print("=" * 60)
    print(f"Начинаем асинхронный парсинг вакансий: {config['query']}")
    print("=" * 60)

    # 1. Асинхронный парсинг вакансий
    vacancies = parse_vacancies_async(
        query=config['query'],
        area=config['area'],
        max_vacancies=config['max_vacancies'],
        max_concurrent=config['max_concurrent']
    )

    if not vacancies:
        print("❌ Вакансии не найдены")
        return

    # Сохранение сырых данных
    print("\n💾 Сохраняем сырые данные...")
    with open('result/vacancies_raw.json', 'w', encoding='utf-8') as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)

    # 2. Анализ данных
    print("\n📊 Анализируем данные...")
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение обработанных данных
    df.to_csv('result/vacancies_processed.csv', index=False, encoding='utf-8-sig')
    print(f"✅ Сохранено {len(df)} обработанных вакансий")

    # 3. Статистика
    print("\n" + "=" * 60)
    print(f"СТАТИСТИКА ПО ВАКАНСИЯМ: {config['query']}")
    print("=" * 60)
    print(f"Всего вакансий: {len(df)}")

    # Навыки
    print("\n📌 Топ-20 навыков:")
    print("-" * 60)
    skills_df = analyzer.analyze_skills()
    print(skills_df.head(20).to_string(index=False))
    skills_df.to_csv('result/skills_analysis.csv', index=False, encoding='utf-8-sig')

    # Требования
    print("\n📌 Топ-20 требований:")
    print("-" * 60)
    requirements_df = analyzer.analyze_requirements()
    print(requirements_df.head(20).to_string(index=False))
    requirements_df.to_csv('result/requirements_analysis.csv', index=False, encoding='utf-8-sig')

    # Зарплаты
    print("\n💰 Статистика по зарплатам:")
    print("-" * 60)
    salary_stats = analyzer.get_salary_stats()
    for key, value in salary_stats.items():
        if isinstance(value, (int, float)):
            print(f"{key}: {value:,.0f}")
        else:
            print(f"{key}: {value}")

    # Опыт
    print("\n👔 Требуемый опыт:")
    print("-" * 60)
    print(df['experience'].value_counts().to_string())

    # 4. Визуализация
    print("\n📈 Создаем визуализации...")
    visualize_results(analyzer)

    print("\n" + "=" * 60)
    print("✅ АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 60)
    print("\nСохраненные файлы:")
    print("  • vacancies_raw.json - сырые данные")
    print("  • vacancies_processed.csv - обработанные данные")
    print("  • skills_analysis.csv - анализ навыков")
    print("  • requirements_analysis.csv - анализ требований")
    print("  • top_skills.png - график навыков")
    print("  • top_requirements.png - график требований")
    print("  • experience_distribution.png - график опыта")


if __name__ == "__main__":
    main()
