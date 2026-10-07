@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Fichiers modifies :
git status --short
echo.

set "MSG=%~1"
if "%MSG%"=="" set /p MSG=Message du commit :
if "%MSG%"=="" (
    echo Message vide, commit annule.
    pause
    exit /b 1
)

git add -A
git commit -m "%MSG%"
echo.
pause
