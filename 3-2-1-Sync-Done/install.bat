@echo off

cd /d "%~dp0"
echo Creating virtual environment for 3-2-1 Sync Done...
python -m venv .venv

if %errorlevel% neq 0 (
    echo Failed to create the virtual environment.
    echo Please make sure Python is installed and available in PATH.
    pause
    exit /b 1
)

echo Installing dependencies for 3-2-1 Sync Done...
.venv\Scripts\python.exe -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo Installation complete!
echo 3-2-1 Sync Done! Will Now Launch!
.venv\Scripts\python.exe "main-control.py"

echo.
echo Application finished.
pause