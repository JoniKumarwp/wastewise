@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 bootstrap.py
) else (
  python bootstrap.py
)
if errorlevel 1 (
  echo.
  echo Setup or startup failed. Read the message above and START_HERE.md.
  pause
)
