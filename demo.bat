@echo off
REM Usage : demo.bat [camera|keyboard]
cd /d "%~dp0"

set MODE=%1
if "%MODE%"=="" set MODE=camera
if not "%MODE%"=="camera" if not "%MODE%"=="keyboard" (
    echo Mode inconnu : %MODE%
    echo Utilisation : demo.bat camera  ou  demo.bat keyboard
    exit /b 1
)

netstat -an | find ":1883 " >nul
if errorlevel 1 (
    echo Erreur : le broker MQTT ne tourne pas sur le port 1883.
    pause
    exit /b 1
)

echo Demarrage des services...
start "Emotion" cmd /k python emotion.py
start "DJ" cmd /k python dj.py
timeout /t 5 /nobreak >nul

echo Connexion des services (mode %MODE%)...
python configure.py %MODE%

if "%MODE%"=="keyboard" (
    start "KeyboardCamera" cmd /k python keyboard_camera.py
) else (
    start "Camera" cmd /k python camera.py
)

if "%MODE%"=="keyboard" (echo Emotion, DJ et KeyboardCamera sont lances :^)) else (echo Emotion, DJ et Camera sont lances :^))
pause
