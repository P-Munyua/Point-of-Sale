@echo off
cd C:\Users\admin\CODE\POINT-OF-SALE
call venv\Scripts\activate.bat
python gunicorn_service.py
pause