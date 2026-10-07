@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Ferme Thunderbird avant de continuer.
pause
python aide.py --epure
echo.
pause
