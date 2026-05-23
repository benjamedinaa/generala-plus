@echo off
setlocal
title GENERALA PLUS - Casino Table Mode
color 0F
cd /d "%~dp0"

echo.
echo ============================================================
echo   GENERALA PLUS
echo   Casino Table Mode
echo ============================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% --version >nul 2>nul
if errorlevel 1 (
    echo No encontre Python instalado.
    echo Instala Python 3.11 o superior desde https://www.python.org/downloads/
    pause
    exit /b 1
)

%PYTHON_CMD% -c "import pygame" >nul 2>nul
if errorlevel 1 (
    echo Instalando dependencias de Generala Plus...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -m generala_plus
if errorlevel 1 (
    echo.
    echo El juego se cerro con un error.
    pause
)
