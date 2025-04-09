@setlocal
@echo on
call .venv\Scripts\activate.bat
pyqt6-tools.exe designer
call .venv\Scripts\deactivate.bat
@endlocal
