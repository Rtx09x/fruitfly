@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  if defined FRUITFLY_PYTHON (
    "%FRUITFLY_PYTHON%" -m venv .venv
  ) else (
    py -3 -m venv .venv 2>nul || python -m venv .venv
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo Python 3 was not found. Set FRUITFLY_PYTHON to its full path.
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
".venv\Scripts\python.exe" run.py %*
