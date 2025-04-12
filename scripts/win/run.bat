@setlocal
@echo on

rem This script should be executed from the root of the repository

call scripts\win\create_venv.bat
call .venv\Scripts\activate.bat
python src\log_viewer\log_viewer.py
call .venv\Scripts\deactivate.bat

exit /b %ERRORLEVEL%

@endlocal
