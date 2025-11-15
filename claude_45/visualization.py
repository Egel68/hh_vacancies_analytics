import matplotlib.pyplot as plt
import seaborn as sns
from processing import VacancyAnalyzer

plt.rcParams['figure.figsize'] = (12, 6)
sns.set_style("whitegrid")

# Для отображения русского текста
plt.rcParams['font.family'] = 'DejaVu Sans'


def visualize_results(analyzer: VacancyAnalyzer):
    """Визуализация результатов анализа"""

    # 1. Top навыков
    skills_df = analyzer.analyze_skills()

    plt.figure(figsize=(14, 8))
    top_skills = skills_df.head(20)
    plt.barh(range(len(top_skills)), top_skills['Количество'])
    plt.yticks(range(len(top_skills)), top_skills['Навык'])
    plt.xlabel('Количество упоминаний')
    plt.title('Топ-20 навыков в вакансиях')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('result/top_skills.png', dpi=300, bbox_inches='tight')
    plt.show()

    # 2. Top требований
    requirements_df = analyzer.analyze_requirements()

    plt.figure(figsize=(14, 8))
    top_req = requirements_df.head(20)
    plt.barh(range(len(top_req)), top_req['Количество'])
    plt.yticks(range(len(top_req)), top_req['Требование'])
    plt.xlabel('Количество упоминаний')
    plt.title('Топ-20 требований в вакансиях')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('result/top_requirements.png', dpi=300, bbox_inches='tight')
    plt.show()

    # 3. Распределение по опыту
    plt.figure(figsize=(10, 6))
    exp_counts = analyzer.df['experience'].value_counts()
    plt.pie(exp_counts.values, labels=exp_counts.index, autopct='%1.1f%%')
    plt.title('Распределение вакансий по требуемому опыту')
    plt.tight_layout()
    plt.savefig('result/experience_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()
