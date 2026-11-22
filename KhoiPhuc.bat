@echo off
chcp 65001 >nul
cd /d "%~dp0"
set /p GAME=Keo tha thu muc game vao day roi bam Enter: 
python patch.py %GAME% --restore
pause
