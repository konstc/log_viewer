@setlocal
@echo off

rem This script should be executed from the root of the repository

call scripts\win\create_venv.bat
call .venv\Scripts\activate.bat
set PYTHONPATH=src\log_viewer
pytest
call .venv\Scripts\deactivate.bat

exit /b %ERRORLEVEL%

@endlocal
