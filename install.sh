#!/bin/bash

echo "============================================================"
echo "  Установка системы ЭДО \"Первый ключ\""
echo "============================================================"
echo

echo "[1/7] Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python 3 не установлен!"
    exit 1
fi
python3 --version

echo
echo "[2/7] Создание виртуального окружения..."
python3 -m venv venv

echo
echo "[3/7] Активация виртуального окружения..."
source venv/bin/activate

echo
echo "[4/7] Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "[5/7] Создание директорий для медиа..."
mkdir -p media/documents
mkdir -p media/avatars

echo
echo "[6/7] Применение миграций базы данных..."
python manage.py makemigrations
python manage.py migrate

echo
echo "[7/7] Инициализация тестовых данных..."
python init_data.py

echo
echo "============================================================"
echo "  Установка завершена успешно!"
echo "============================================================"
echo
echo "Для запуска сервера выполните: ./start_server.sh"
echo "Или вручную: python manage.py runserver"
echo
