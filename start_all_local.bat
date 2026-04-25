@echo off
echo ========================================
echo Starting TeqMates Local Environment
echo ========================================
echo.

REM Start Backend
start "Backend (8011)" cmd /k "cd ResortApp && venv\Scripts\activate && python main.py"

REM Wait for backend
ping 127.0.0.1 -n 6 >nul

REM Start Admin Dashboard
start "Admin Dashboard (3000)" cmd /k "cd dasboard && npm start"

REM Wait a bit
ping 127.0.0.1 -n 3 >nul

REM Start User End
start "User End (3002)" cmd /k "cd userend && npm start"

echo.
echo ========================================
echo All systems are starting!
echo Backend:  http://localhost:8011
echo Admin:    http://localhost:3000
echo User:     http://localhost:3002
echo ========================================
echo.
pause
