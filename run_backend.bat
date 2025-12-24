@echo off
echo Starting Zap Quick Backend...
call venv\Scripts\activate
uvicorn src.backend.main:app --reload
pause
