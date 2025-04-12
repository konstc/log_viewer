@setlocal
@echo off

rem This script should be executed from the root of the repository

for /f "delims= eol=|" %%a in ('python --version ^| findstr " 3.9"') do @set PYTHON_VALID=%%a

if "x%PYTHON_VALID%" == "x" (
    echo Installed python version is not supported. Please install python v.3.9.x.
    exit /b 1
)

if not exist .venv (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    call .venv\Scripts\deactivate.bat
    echo Python virtual environment is created in .venv
) else (
    echo Python virtual environment already exists
)

exit /b %ERRORLEVEL%

@endlocal
