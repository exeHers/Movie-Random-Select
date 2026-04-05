@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo No virtual environment yet - running setup first ...
  echo.
  call "%~dp0setup.bat" silent
  if errorlevel 1 exit /b 1
  echo.
)

REM Repair incomplete venv (e.g. setup stopped before pip install)
".venv\Scripts\python.exe" -c "import uvicorn" 2>nul
if errorlevel 1 (
  echo Installing Python dependencies ^(uvicorn was missing^) ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] pip install failed. Check your network and try again.
    pause
    exit /b 1
  )
  echo.
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env - add your TMDB API key, then run this file again.
  echo Opening Notepad ...
  start "" notepad ".env"
  echo.
  echo Get a key: https://www.themoviedb.org/settings/api
  pause
  exit /b 1
)

findstr /r /c:"^TMDB_API_KEY=." ".env" >nul 2>&1
if errorlevel 1 (
  echo TMDB_API_KEY is missing or empty in .env
  echo Opening .env - paste your key from https://www.themoviedb.org/settings/api
  echo.
  start "" notepad ".env"
  pause
  exit /b 1
)

echo Movie Night - http://127.0.0.1:8000
echo Opening your browser in a few seconds ... Leave this window open. Press Ctrl+C to stop.
echo.
start /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000/"
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
pause
