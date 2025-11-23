import os
import re
from pathlib import Path


def remove_comments_and_empty_lines(content, file_extension):
    """
    Удаляет комментарии и пустые строки в зависимости от типа файла.

    Args:
        content: Содержимое файла
        file_extension: Расширение файла (например, '.py', '.js')

    Returns:
        Очищенное содержимое
    """
    lines = content.split('\n')
    cleaned_lines = []

    # Определяем тип комментариев по расширению файла
    if file_extension in ['.py']:
        # Python комментарии
        in_multiline = False
        multiline_quote = None

        for line in lines:
            stripped = line.strip()

            # Обработка многострочных комментариев (docstrings)
            if not in_multiline:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    multiline_quote = '"""' if '"""' in stripped else "'''"
                    # Проверяем, закрывается ли на той же строке
                    if stripped.count(multiline_quote) >= 2:
                        continue
                    in_multiline = True
                    continue
                # Пропускаем строки с комментариями
                elif stripped.startswith('#'):
                    continue
                # Удаляем инлайн комментарии
                elif '#' in line:
                    code_part = line.split('#')[0].rstrip()
                    if code_part:  # Если есть код до комментария
                        cleaned_lines.append(code_part)
                    continue
                # Пропускаем пустые строки
                elif not stripped:
                    continue
                else:
                    cleaned_lines.append(line)
            else:
                # Ищем закрывающую кавычку
                if multiline_quote in stripped:
                    in_multiline = False
                continue

    elif file_extension in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cs', '.php']:
        # JavaScript, TypeScript, Java, C/C++, C#, PHP комментарии
        content_no_multiline = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        lines = content_no_multiline.split('\n')

        for line in lines:
            stripped = line.strip()
            # Пропускаем строки с комментариями
            if stripped.startswith('//'):
                continue
            # Удаляем инлайн комментарии
            elif '//' in line:
                code_part = line.split('//')[0].rstrip()
                if code_part:
                    cleaned_lines.append(code_part)
                continue
            # Пропускаем пустые строки
            elif not stripped:
                continue
            else:
                cleaned_lines.append(line)

    elif file_extension in ['.html', '.xml', '.svg']:
        # HTML/XML комментарии
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        lines = content.split('\n')
        cleaned_lines = [line for line in lines if line.strip()]

    elif file_extension in ['.css', '.scss', '.sass']:
        # CSS комментарии
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        lines = content.split('\n')
        cleaned_lines = [line for line in lines if line.strip()]

    elif file_extension in ['.sh', '.bash', '.yaml', '.yml']:
        # Shell, YAML комментарии
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            elif '#' in line:
                code_part = line.split('#')[0].rstrip()
                if code_part:
                    cleaned_lines.append(code_part)
                continue
            elif not stripped:
                continue
            else:
                cleaned_lines.append(line)

    elif file_extension in ['.sql']:
        # SQL комментарии
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        lines = content.split('\n')

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            elif '--' in line:
                code_part = line.split('--')[0].rstrip()
                if code_part:
                    cleaned_lines.append(code_part)
                continue
            elif not stripped:
                continue
            else:
                cleaned_lines.append(line)

    else:
        # Для неизвестных типов просто удаляем пустые строки
        cleaned_lines = [line for line in lines if line.strip()]

    return '\n'.join(cleaned_lines)


def collect_files(
        root_dir,
        output_file='output.txt',
        ignore_files=None,
        ignore_dirs=None,
        remove_comments=False  # Новый параметр
):
    """
    Рекурсивно проходит по директориям и собирает содержимое файлов.

    Args:
        root_dir: Корневая директория для поиска
        output_file: Файл для сохранения результата
        ignore_files: Список имен файлов для игнорирования
        ignore_dirs: Список имен директорий для игнорирования
        remove_comments: Если True, удаляет комментарии и пустые строки
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
                status = "🧹" if remove_comments else "✅"
                print(f"{status} Обработка: {relative_path}")
                processed_files.append(str(relative_path))

                # Записываем название файла
                out.write(f"Файл: {relative_path}\n")

                # Пытаемся прочитать и записать содержимое
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Если нужно удалить комментарии
                        if remove_comments:
                            file_extension = file_path.suffix.lower()
                            content = remove_comments_and_empty_lines(content, file_extension)

                        out.write(content)
                except UnicodeDecodeError:
                    # Если файл бинарный, пробуем другую кодировку или пропускаем
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            content = f.read()

                            if remove_comments:
                                file_extension = file_path.suffix.lower()
                                content = remove_comments_and_empty_lines(content, file_extension)

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
    if remove_comments:
        print(f"Режим: Комментарии и пустые строки удалены")
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
        ],
        remove_comments=True  # Установите True для удаления комментариев
    )
