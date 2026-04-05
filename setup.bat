@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo Movie Night - setup (venv + Python packages + .env file)
echo.

where py >nul 2>&1
if !errorlevel! equ 0 (
  set "VENV_CMD=py -3 -m venv .venv"
) else (
  where python >nul 2>&1
  if !errorlevel! neq 0 (
    echo [ERROR] Python 3 not found.
    echo Install from https://www.python.org/downloads/  ^(64-bit^)
    echo During setup, CHECK "Add python.exe to PATH".
    if /i not "%~1"=="silent" pause
    exit /b 1
  )
  set "VENV_CMD=python -m venv .venv"
)

echo Creating virtual environment in .venv ...
%VENV_CMD%
if errorlevel 1 (
  echo [ERROR] Could not create .venv
  if /i not "%~1"=="silent" pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your network and try again.
  if /i not "%~1"=="silent" pause
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env from .env.example
) else (
  echo .env already exists - left unchanged
)

echo.
echo Setup finished successfully.
if /i "%~1"=="silent" (
  echo.
  exit /b 0
)

echo.
echo NEXT STEPS:
echo   1. Open the file named .env in this folder.
echo   2. Set TMDB_API_KEY=your_key  ^(no quotes^)
echo      Get a free key: https://www.themoviedb.org/settings/api
echo   3. Double-click run.bat or start.bat to launch the app.
echo   4. Open http://127.0.0.1:8000 in your browser.
echo      The green "Healthy" badge means the server and database are OK.
echo.
pause
exit /b 0
