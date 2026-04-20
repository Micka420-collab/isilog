@echo off
setlocal
cd /d %~dp0\..
call .venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm --windowed --name IsilogLocalAssistant --add-data "config;config" --add-data "app/prompts;app/prompts" app/main.py
echo Build termine. Executable: dist\IsilogLocalAssistant\IsilogLocalAssistant.exe
endlocal
