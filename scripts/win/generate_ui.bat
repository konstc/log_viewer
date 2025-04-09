@setlocal
call .venv\Scripts\activate.bat
pyuic6.exe -d -o src\log_viewer\generated_ui\ui_about_dialog.py forms\AboutDialog.ui
pyuic6.exe -d -o src\log_viewer\generated_ui\ui_import_dialog.py forms\ImportDialog.ui
pyuic6.exe -d -o src\log_viewer\generated_ui\ui_main_window.py forms\MainWindow.ui
pyuic6.exe -d -o src\log_viewer\generated_ui\ui_settings_dialog.py forms\SettingsDialog.ui
call .venv\Scripts\deactivate.bat
@endlocal
