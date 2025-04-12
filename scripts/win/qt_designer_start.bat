@setlocal
@echo off

rem This script should be executed from the root of the repository

call scripts\win\create_venv.bat
call .venv\Scripts\activate.bat
pyqt6-tools.exe designer
call .venv\Scripts\deactivate.bat

exit /b %ERRORLEVEL%

@endlocal
