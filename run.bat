@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo Сначала запусти install.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
echo Бот запущен. Не закрывай это окно. Остановка: Ctrl+C или закрой окно.
echo.
python -m bot.main
pause
