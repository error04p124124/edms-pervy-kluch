@echo off
chcp 65001 >nul
echo ============================================================
echo   Установка системы ЭДО "Первый ключ"
echo ============================================================
echo.

echo [1/7] Проверка Python...
Py --version
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Скачайте Python 3.10+ с https://www.python.org/
    pause
    exit /b 1
)

echo.
echo [2/7] Создание виртуального окружения...
Py -m venv venv
if errorlevel 1 (
    echo ОШИБКА: Не удалось создать виртуальное окружение!
    pause
    exit /b 1
)

echo.
echo [3/7] Активация виртуального окружения...
call .\venv\Scripts\activate

echo.
echo [4/7] Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости!
    pause
    exit /b 1
)

echo.
echo [5/7] Создание директорий для медиа...
if not exist "media" mkdir media
if not exist "media\documents" mkdir media\documents
if not exist "media\avatars" mkdir media\avatars

echo.
echo [6/7] Применение миграций базы данных...
python manage.py makemigrations
python manage.py migrate
if errorlevel 1 (
    echo ОШИБКА: Не удалось применить миграции!
    pause
    exit /b 1
)

echo.
echo [7/7] Инициализация тестовых данных...
python init_data.py

echo.
echo ============================================================
echo   Установка завершена успешно!
echo ============================================================
echo.
echo Для запуска сервера выполните: start_server.bat
echo Или вручную: python manage.py runserver
echo.
pause
