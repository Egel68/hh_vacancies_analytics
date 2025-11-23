import os
from pathlib import Path


def collect_files(
        root_dir,
        output_file='output.txt',
        ignore_files=None,
        ignore_dirs=None
):
    """
    Рекурсивно проходит по директориям и собирает содержимое файлов.

    Args:
        root_dir: Корневая директория для поиска
        output_file: Файл для сохранения результата
        ignore_files: Список имен файлов для игнорирования
        ignore_dirs: Список имен директорий для игнорирования
    """
    if ignore_files is None:
        ignore_files = []
    if ignore_dirs is None:
        ignore_dirs = []

    # ВАЖНО: Автоматически добавляем выходной файл в игнорируемые
    output_filename = Path(output_file).name
    if output_filename not in ignore_files:
        ignore_files.append(output_filename)

    root_path = Path(root_dir)
    processed_files = []

    with open(output_file, 'w', encoding='utf-8') as out:
        for current_dir, dirs, files in os.walk(root_path):
            # Удаляем игнорируемые директории из обхода
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            current_path = Path(current_dir)

            for file in files:
                # Пропускаем игнорируемые файлы
                if file in ignore_files:
                    print(f"⏭️  Пропущен (в ignore): {file}")
                    continue

                file_path = current_path / file
                relative_path = file_path.relative_to(root_path)

                # Логируем обрабатываемый файл
                print(f"✅ Обработка: {relative_path}")
                processed_files.append(str(relative_path))

                # Записываем название файла
                # out.write(f"{'=' * 80}\n")
                out.write(f"Файл: {relative_path}\n")
                # out.write(f"{'=' * 80}\n\n")

                # Пытаемся прочитать и записать содержимое
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        out.write(content)
                except UnicodeDecodeError:
                    # Если файл бинарный, пробуем другую кодировку или пропускаем
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            content = f.read()
                            out.write(content)
                    except:
                        out.write("[Не удалось прочитать файл - возможно, это бинарный файл]\n")
                        print(f"⚠️  Бинарный файл: {relative_path}")
                except Exception as e:
                    out.write(f"[Ошибка при чтении файла: {e}]\n")
                    print(f"❌ Ошибка: {relative_path} - {e}")

                out.write(f"\n\n")

    print(f"\n{'=' * 80}")
    print(f"Готово! Результат сохранен в {output_file}")
    print(f"Обработано файлов: {len(processed_files)}")
    print(f"{'=' * 80}")


# Пример использования
if __name__ == "__main__":
    collect_files(
        root_dir='..',  # Текущая директория
        output_file='promt.txt',
        ignore_files=[
            'architecture.md',
            'README.md',
            'script_promt.py',
            '.gitignore',
        ],
        ignore_dirs=[
            '.git',
            '__pycache__',
            'node_modules',
            '.venv',
            'venv',
            '.ipynb_checkpoints',
            '.idea',
            'R&D',
            'result'
        ]
    )
