@echo off
echo ================================================
echo   Загрузка тестовых данных для ЭДО "Первый ключ"
echo ================================================
echo.

cd /d %~dp0

call venv\Scripts\activate.bat

echo Запуск команды загрузки тестовых данных...
echo.

python manage.py load_test_data --users=50 --documents=200

echo.
echo ================================================
echo   Загрузка завершена!
echo ================================================
echo.
echo Данные для входа:
echo - admin / admin
echo - Другие пользователи: фамилия.имя[цифра] / test123
echo   Например: ivanov.aleksandr1 / test123
echo.
pause
