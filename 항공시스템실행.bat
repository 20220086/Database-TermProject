@echo off
cd /d "C:\Users\길상준\OneDrive\바탕 화면\term"
call .venv\Scripts\activate.bat
uv run python app.py
pause