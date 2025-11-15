from getData import HHParser
from processing import VacancyAnalyzer
from visualization import visualize_results
import json


def main():
    # 1. Парсинг вакансий
    parser = HHParser()
    query = "Python разработчик"  # Измените на нужную должность

    vacancies = parser.parse_vacancies(
        query=query,
        area=1,  # Москва
        max_vacancies=100  # Количество вакансий для анализа
    )

    # Сохранение сырых данных
    with open('./result/vacancies_raw.json', 'w', encoding='utf-8') as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)

    # 2. Анализ
    analyzer = VacancyAnalyzer(vacancies)
    df = analyzer.extract_data()

    # Сохранение обработанных данных
    df.to_csv('./result/vacancies_processed.csv', index=False, encoding='utf-8-sig')

    # 3. Получение статистики
    print("\n" + "=" * 50)
    print(f"Всего вакансий: {len(df)}")
    print("=" * 50)

    # Навыки
    skills_df = analyzer.analyze_skills()
    print("\nТоп-20 навыков:")
    print(skills_df.head(20).to_string(index=False))
    skills_df.to_csv('./result/skills_analysis.csv', index=False, encoding='utf-8-sig')

    # Требования
    requirements_df = analyzer.analyze_requirements()
    print("\nТоп-20 требований:")
    print(requirements_df.head(20).to_string(index=False))
    requirements_df.to_csv('./result/requirements_analysis.csv', index=False, encoding='utf-8-sig')

    # Зарплаты
    salary_stats = analyzer.get_salary_stats()
    print("\nСтатистика по зарплатам:")
    for key, value in salary_stats.items():
        print(f"{key}: {value}")

    # 4. Визуализация
    visualize_results(analyzer)

    print("\n✅ Анализ завершен! Файлы сохранены.")


if __name__ == "__main__":
    main()
