@echo off
echo ============================================================
echo WooCommerce - Odoo Connector
echo ============================================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo .env file created. Please edit it with your credentials.
    echo.
    pause
    exit /b 1
)

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Create logs directory
if not exist logs mkdir logs

REM Run the application
echo Starting connector...
echo.
python run.py

pause
