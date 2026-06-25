@echo off
echo Starting ReadLens Application...

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    C:\Users\USER\AppData\Local\Python\pythoncore-3.14-64\python.exe -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python app.py
pause
