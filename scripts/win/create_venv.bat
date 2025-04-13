@setlocal
@echo off

rem This script should be executed from the root of the repository

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
