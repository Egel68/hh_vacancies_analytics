"""
Модуль визуализации результатов анализа.
Следует принципу Single Responsibility - только визуализация.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from pathlib import Path
from core.interfaces import IVacancyVisualizer, IVacancyAnalyzer

# Настройка для русского языка
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.figsize'] = (12, 6)
sns.set_style("whitegrid")


class VacancyVisualizer(IVacancyVisualizer):
    """Визуализатор результатов анализа вакансий."""

    def visualize(
            self,
            analyzer: IVacancyAnalyzer,
            output_dir: str,
            show_plots: bool = False
    ) -> None:
        """
        Создание и сохранение всех визуализаций.

        Args:
            analyzer: Анализатор с данными
            output_dir: Директория для сохранения
            show_plots: Показывать ли графики
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n📈 Создаем визуализации...")

        self._create_skills_chart(analyzer, output_path, show_plots)
        self._create_requirements_chart(analyzer, output_path, show_plots)
        self._create_experience_chart(analyzer, output_path, show_plots)

    def _create_skills_chart(
            self,
            analyzer: IVacancyAnalyzer,
            output_path: Path,
            show_plots: bool
    ) -> None:
        """Создание диаграммы навыков."""
        skills_df = analyzer.analyze_skills()

        if len(skills_df) > 0:
            plt.figure(figsize=(14, 8))
            top_skills = skills_df.head(20)
            colors = sns.color_palette("viridis", len(top_skills))

            plt.barh(
                range(len(top_skills)),
                top_skills['Количество'],
                color=colors
            )
            plt.yticks(range(len(top_skills)), top_skills['Навык'])
            plt.xlabel('Количество упоминаний', fontsize=12)
            plt.title(
                'Топ-20 навыков в вакансиях',
                fontsize=14,
                fontweight='bold'
            )
            plt.gca().invert_yaxis()

            for i, v in enumerate(top_skills['Количество']):
                plt.text(v + 0.3, i, str(v), va='center', fontsize=9)

            plt.tight_layout()
            plt.savefig(
                output_path / 'top_skills.png',
                dpi=300,
                bbox_inches='tight'
            )

            if show_plots:
                plt.show()

            plt.close()
            print(f"  ✅ График навыков сохранен")

    def _create_requirements_chart(
            self,
            analyzer: IVacancyAnalyzer,
            output_path: Path,
            show_plots: bool
    ) -> None:
        """Создание диаграммы требований."""
        requirements_df = analyzer.analyze_requirements()

        if len(requirements_df) > 0:
            plt.figure(figsize=(14, 8))
            top_req = requirements_df.head(20)
            colors = sns.color_palette("rocket", len(top_req))

            plt.barh(
                range(len(top_req)),
                top_req['Количество'],
                color=colors
            )
            plt.yticks(range(len(top_req)), top_req['Требование'])
            plt.xlabel('Количество упоминаний', fontsize=12)
            plt.title(
                'Топ-20 требований в вакансиях',
                fontsize=14,
                fontweight='bold'
            )
            plt.gca().invert_yaxis()

            for i, v in enumerate(top_req['Количество']):
                plt.text(v + 0.3, i, str(v), va='center', fontsize=9)

            plt.tight_layout()
            plt.savefig(
                output_path / 'top_requirements.png',
                dpi=300,
                bbox_inches='tight'
            )

            if show_plots:
                plt.show()

            plt.close()
            print(f"  ✅ График требований сохранен")

    def _create_experience_chart(
            self,
            analyzer: IVacancyAnalyzer,
            output_path: Path,
            show_plots: bool
    ) -> None:
        """Создание диаграммы распределения опыта."""
        if analyzer.df is None:
            analyzer.extract_data()

        if 'experience' in analyzer.df.columns:
            plt.figure(figsize=(10, 6))
            exp_counts = analyzer.df['experience'].value_counts()

            if len(exp_counts) > 0:
                colors = sns.color_palette("pastel", len(exp_counts))
                wedges, texts, autotexts = plt.pie(
                    exp_counts.values,
                    labels=exp_counts.index,
                    autopct='%1.1f%%',
                    colors=colors,
                    startangle=90
                )

                for text in texts:
                    text.set_fontsize(11)

                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(10)

                plt.title(
                    'Распределение вакансий по требуемому опыту',
                    fontsize=14,
                    fontweight='bold'
                )
                plt.tight_layout()
                plt.savefig(
                    output_path / 'experience_distribution.png',
                    dpi=300,
                    bbox_inches='tight'
                )

                if show_plots:
                    plt.show()

                plt.close()
                print(f"  ✅ График распределения опыта сохранен")
