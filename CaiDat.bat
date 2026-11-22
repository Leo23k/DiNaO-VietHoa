@echo off
chcp 65001 >nul
cd /d "%~dp0"
set /p GAME=Keo tha thu muc game vao day roi bam Enter: 
python -m pip install -q -r requirements.txt || goto :err
python patch.py %GAME%
pause
exit /b
:err
echo Can cai Python 3.10+ tu python.org (tick "Add to PATH").
pause
