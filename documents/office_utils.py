"""
Утилиты для работы с Office документами (Word, Excel, PDF)
"""
import os
import re
from io import BytesIO
from datetime import datetime

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, RGBColor
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def replace_placeholders_in_text(text, replacements):
    """
    Заменяет плейсхолдеры в тексте
    Поддерживает форматы: {{placeholder}}, {placeholder}, [placeholder]
    """
    if not text:
        return text
    
    result = text
    for key, value in replacements.items():
        # Поддержка разных форматов плейсхолдеров
        patterns = [
            r'\{\{' + re.escape(key) + r'\}\}',  # {{key}}
            r'\{' + re.escape(key) + r'\}',       # {key}
            r'\[' + re.escape(key) + r'\]',       # [key]
        ]
        
        for pattern in patterns:
            result = re.sub(pattern, str(value), result, flags=re.IGNORECASE)
    
    return result


def _replace_in_paragraph(paragraph, replacements):
    """
    Заменяет плейсхолдеры в параграфе, собирая весь текст параграфа в одну строку.
    Word часто дробит плейсхолдер {{name}} по нескольким runs—этот метод решает её.
    """
    if not paragraph.runs:
        return
    full_text = ''.join(run.text for run in paragraph.runs)
    new_text = replace_placeholders_in_text(full_text, replacements)
    if new_text != full_text:
        # Переносим весь текст в первый run (сохраняет его форматирование), остальные очищаем
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ''


def generate_word_document(template_path, output_path, replacements):
    """
    Генерирует Word документ из шаблона с заменой плейсхолдеров
    
    Args:
        template_path: путь к файлу шаблона .docx
        output_path: путь для сохранения результата
        replacements: словарь замен {плейсхолдер: значение}
    
    Returns:
        True если успешно, False если ошибка
    """
    if not DOCX_AVAILABLE:
        raise ImportError("Библиотека python-docx не установлена. Установите: pip install python-docx")
    
    try:
        # Открываем шаблон
        doc = DocxDocument(template_path)
        
        # Заменяем в параграфах
        for paragraph in doc.paragraphs:
            _replace_in_paragraph(paragraph, replacements)
        
        # Заменяем в таблицах
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_in_paragraph(paragraph, replacements)
        
        # Заменяем в колонтитулах
        for section in doc.sections:
            # Верхний колонтитул
            header = section.header
            for paragraph in header.paragraphs:
                _replace_in_paragraph(paragraph, replacements)
            
            # Нижний колонтитул
            footer = section.footer
            for paragraph in footer.paragraphs:
                _replace_in_paragraph(paragraph, replacements)
        
        # Сохраняем
        doc.save(output_path)
        return True
    
    except Exception as e:
        print(f"Ошибка генерации Word документа: {e}")
        return False


def generate_excel_document(template_path, output_path, replacements):
    """
    Генерирует Excel документ из шаблона с заменой плейсхолдеров
    
    Args:
        template_path: путь к файлу шаблона .xlsx
        output_path: путь для сохранения результата
        replacements: словарь замен {плейсхолдер: значение}
    
    Returns:
        True если успешно, False если ошибка
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("Библиотека openpyxl не установлена. Установите: pip install openpyxl")
    
    try:
        # Открываем шаблон
        workbook = load_workbook(template_path)
        
        # Проходим по всем листам
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # Проходим по всем ячейкам
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str):
                        cell.value = replace_placeholders_in_text(cell.value, replacements)
        
        # Сохраняем
        workbook.save(output_path)
        return True
    
    except Exception as e:
        print(f"Ошибка генерации Excel документа: {e}")
        return False



def generate_pdf_document(template_path, output_path, replacements):
    """
    Regenerates a ReportLab PDF template with filled placeholder values.
    Works by monkey-patching Canvas.drawString to apply replacements on every text call,
    then re-running the original PDF builder function.
    """
    try:
        from reportlab.pdfgen.canvas import Canvas as _Canvas

        # Map template filename → builder method name in create_template_files.Command
        _BUILDER_MAP = {
            'zayavlenie_otpusk.pdf':      '_make_pdf_zayavlenie',
            'sluzhebnaya_zapiska.pdf':    '_make_pdf_memo',
            'obyasnitelnaya_zapiska.pdf': '_make_pdf_obyasnitelnaya',
            'zayavlenie_priem.pdf':       '_make_pdf_zayavlenie_priem',
        }

        filename = os.path.basename(template_path)
        builder_name = _BUILDER_MAP.get(filename)
        if not builder_name:
            return False, f"Не найден генератор для PDF шаблона: {filename}"

        from documents.management.commands.create_template_files import Command as _Cmd
        cmd = _Cmd()

        # Monkey-patch drawString to apply replacements before drawing
        orig_drawString = _Canvas.drawString

        def _patched_drawString(self, x, y, text, **kwargs):
            replaced = replace_placeholders_in_text(str(text), replacements)
            return orig_drawString(self, x, y, replaced, **kwargs)

        _Canvas.drawString = _patched_drawString
        try:
            getattr(cmd, builder_name)(output_path)
        finally:
            _Canvas.drawString = orig_drawString  # always restore

        return True, None

    except Exception as e:
        print(f"Ошибка генерации PDF документа: {e}")
        return False, str(e)


def generate_document_from_template(template_file_path, template_format, output_path, replacements):
    """
    Универсальная функция генерации документа из шаблона

    Args:
        template_file_path: путь к файлу шаблона
        template_format: формат документа ('docx', 'xlsx', 'pdf')
        output_path: путь для сохранения результата
        replacements: словарь замен {плейсхолдер: значение}

    Returns:
        tuple (success: bool, error_message: str)
    """
    try:
        if template_format == 'docx':
            if not template_file_path or not os.path.exists(template_file_path):
                return False, "Файл шаблона Word не найден"
            success = generate_word_document(template_file_path, output_path, replacements)
            return (True, None) if success else (False, "Ошибка генерации Word документа")

        elif template_format == 'xlsx':
            if not template_file_path or not os.path.exists(template_file_path):
                return False, "Файл шаблона Excel не найден"
            success = generate_excel_document(template_file_path, output_path, replacements)
            return (True, None) if success else (False, "Ошибка генерации Excel документа")

        elif template_format == 'pdf':
            if not template_file_path or not os.path.exists(template_file_path):
                return False, "Файл шаблона PDF не найден"
            return generate_pdf_document(template_file_path, output_path, replacements)

        else:
            return False, f"Неподдерживаемый формат: {template_format}"

    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Непредвиденная ошибка: {str(e)}"


def check_office_libraries():
    """
    Проверяет наличие установленных библиотек для работы с Office
    
    Returns:
        dict с информацией о доступности библиотек
    """
    return {
        'docx': DOCX_AVAILABLE,
        'xlsx': OPENPYXL_AVAILABLE,
        'all_available': DOCX_AVAILABLE and OPENPYXL_AVAILABLE
    }
