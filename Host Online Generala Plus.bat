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
echo Este archivo abre SOLO el servidor.
echo Para jugar desde esta misma PC, abre tambien:
echo   Unirse Online Generala Plus.bat
echo y usa la IP 127.0.0.1.
echo.
echo IPs de esta PC para pasarle a tu amigo:
ipconfig | findstr /R /C:"IPv4"
echo.
echo Puerto: 8765
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -m generala_plus.net.server --host 0.0.0.0 --port 8765
pause
