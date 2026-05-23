@echo off
setlocal
title GENERALA PLUS - HOST Y JUGAR
color 0F
cd /d "%~dp0"

echo.
echo ============================================================
echo   GENERALA PLUS - HOST Y JUGAR ONLINE
echo ============================================================
echo.
echo Esto abre el servidor en otra ventana y luego te conecta como jugador.
echo Pasale a tu amigo una de estas IPv4 y el puerto 8765:
ipconfig | findstr /R /C:"IPv4"
echo.
set /p PLAYER_NAME=Tu nombre: 
if "%PLAYER_NAME%"=="" set "PLAYER_NAME=Host"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

start "GENERALA PLUS - SERVIDOR ONLINE" cmd /k %PYTHON_CMD% -m generala_plus.net.server --host 0.0.0.0 --port 8765
timeout /t 2 /nobreak >nul
%PYTHON_CMD% -m generala_plus.net.client --host 127.0.0.1 --port 8765 --name "%PLAYER_NAME%"
pause
