@echo off
setlocal
title GENERALA PLUS - HOST ONLINE
color 0F
cd /d "%~dp0"

echo.
echo ============================================================
echo   GENERALA PLUS - HOST ONLINE
echo ============================================================
echo.
echo Este modo online es basico y funciona por LAN o VPN.
echo Compartí tu IP y el puerto 8765 con el otro jugador.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -m generala_plus.net.server --host 0.0.0.0 --port 8765
pause
