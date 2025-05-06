import os
import re
from datetime import datetime

def find_style_classes(directory):
    style_pattern = re.compile(r'class=["\']([^"\']+)["\']')
    html_pattern = re.compile(r'\.(html|htm|php|jsx|tsx|vue)$', re.IGNORECASE)
    valid_class_pattern = re.compile(r'^-?[a-zA-Z_][a-zA-Z0-9_-]*$')
    
    report_data = []
    total_styles = 0
    scanned_dirs = {}
    unique_styles = set()
    
    for root, dirs, files in os.walk(directory):
        dir_styles = 0
        for file in files:
            if html_pattern.search(file):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Удаляем PHP/JS код чтобы не мешал анализу
                        clean_content = re.sub(r'<\?php.*?\?>', '', content, flags=re.DOTALL)
                        clean_content = re.sub(r'\{%.*?%\}', '', clean_content, flags=re.DOTALL)
                        clean_content = re.sub(r'\{\{.*?\}\}', '', clean_content, flags=re.DOTALL)
                        
                        for line_num, line in enumerate(clean_content.split('\n'), 1):
                            matches = style_pattern.finditer(line)
                            for match in matches:
                                classes = match.group(1).split()
                                for class_name in classes:
                                    # Извлекаем первый класс (до пробела если несколько)
                                    first_class = class_name.split()[0].strip()
                                    
                                    # Пропускаем если:
                                    # 1. Содержит спецсимволы ($, <?, ?> и т.д.)
                                    # 2. Не соответствует формату CSS-класса
                                    # 3. Является строкой форматирования (%s)
                                    if (re.search(r'[$\?<>{}()%]', first_class) or 
                                        not valid_class_pattern.match(first_class)):
                                        continue
                                    
                                    if first_class:
                                        unique_styles.add(first_class)
                                        
                                        # Находим тег
                                        tag_start = line.rfind('<', 0, match.start())
                                        tag_end = line.find('>', match.start())
                                        if tag_start != -1 and tag_end != -1:
                                            full_tag = line[tag_start:tag_end+1]
                                            
                                            report_data.append({
                                                'class': first_class,
                                                'tag': full_tag.strip(),
                                                'filepath': filepath,
                                                'line_number': line_num
                                            })
                                            dir_styles += 1
                                            total_styles += 1
                except Exception as e:
                    print(f"Ошибка при обработке файла {filepath}: {e}")
        
        scanned_dirs[root] = dir_styles
    
    return {
        'report_data': report_data,
        'total_styles': total_styles,
        'scanned_dirs': scanned_dirs,
        'unique_styles': sorted(unique_styles)
    }

def generate_report(data, directory):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    dir_name = os.path.basename(os.path.normpath(directory))
    report_filename = f"report-{dir_name}-{now.strftime('%Y%m%d-%H%M%S')}.txt"
    
    report_lines = []
    
    # Заголовок отчета
    report_lines.append(f"Отчет о поиске классов стилей")
    report_lines.append(f"Дата и время: {timestamp}")
    report_lines.append(f"Папка с файлами: {directory}")
    report_lines.append(f"Всего найдено стилей: {data['total_styles']}")
    report_lines.append(f"Уникальных стилей: {len(data['unique_styles'])}")
    report_lines.append(f"Уникальные стили: {', '.join(data['unique_styles'])}\n")
    
    # Просмотренные папки
    report_lines.append("Просмотренные папки:")
    for dir_path, count in data['scanned_dirs'].items():
        report_lines.append(f"- {dir_path} (найдено стилей: {count})")
    
    # Основные данные
    report_lines.append("\nНайденные классы стилей:")
    for item in data['report_data']:
        report_lines.append(f"{item['class']}; {item['tag']}; строка {item['line_number']}; {item['filepath']}")
    
    # Создаем папку reports
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Полный путь к файлу отчета
    report_path = os.path.join(reports_dir, report_filename)
    
    return "\n".join(report_lines), report_path

def main():
    directory = input("Введите путь к папке для поиска: ").strip()
    
    if not os.path.isdir(directory):
        print("Указанная папка не существует!")
        return
    
    print("Поиск классов стилей...")
    result = find_style_classes(directory)
    
    report, report_path = generate_report(result, directory)
    
    # Сохраняем отчет
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Отчет сохранен в файл: {report_path}")

if __name__ == "__main__":
    main()