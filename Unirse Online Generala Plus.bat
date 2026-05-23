@echo off
setlocal
title GENERALA PLUS - UNIRSE ONLINE
color 0F
cd /d "%~dp0"

echo.
echo ============================================================
echo   GENERALA PLUS - UNIRSE ONLINE
echo ============================================================
echo.
echo Si sos el host en esta misma PC, usa 127.0.0.1.
echo Si te unis a un amigo, usa la IPv4 que te pase.
echo.
set /p HOST_IP=IP del host ^(ej: 127.0.0.1^): 
if "%HOST_IP%"=="" set "HOST_IP=127.0.0.1"
set /p PLAYER_NAME=Tu nombre: 
if "%PLAYER_NAME%"=="" set "PLAYER_NAME=Jugador"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -m generala_plus.net.client --host "%HOST_IP%" --port 8765 --name "%PLAYER_NAME%"
pause
