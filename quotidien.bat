@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

>> journal.log echo ===== %date% %time% =====
python aide.py --epure >> journal.log 2>&1
git push >> journal.log 2>&1
