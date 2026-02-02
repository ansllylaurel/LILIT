@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Установка бота (один раз)
echo ============================================
if not exist "venv" (
    echo Создаю папку venv...
    python -m venv venv
    if errorlevel 1 (
        echo ОШИБКА: Не найден Python. Установи Python с python.org и отметь "Add to PATH"
        pause
        exit /b 1
    )
) else (
    echo Папка venv уже есть.
)
echo.
echo Устанавливаю библиотеки...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ОШИБКА при установке.
    pause
    exit /b 1
)
if not exist ".env" (
    echo Создаю файл .env из примера...
    copy .env.example .env
    echo Открой файл .env в блокноте и вставь свои токены! См. ПРОСТАЯ_ИНСТРУКЦИЯ.txt
)
echo.
echo ============================================
echo   Готово. Запускай run.bat
echo ============================================
pause
