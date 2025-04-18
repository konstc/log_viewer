#!/bin/bash

source scripts/linux/create_venv.sh
source .venv/bin/activate
pyuic6 -d -o src/log_viewer/generated_ui/ui_about_dialog.py forms/AboutDialog.ui
pyuic6 -d -o src/log_viewer/generated_ui/ui_import_dialog.py forms/ImportDialog.ui
pyuic6 -d -o src/log_viewer/generated_ui/ui_main_window.py forms/MainWindow.ui
pyuic6 -d -o src/log_viewer/generated_ui/ui_settings_dialog.py forms/SettingsDialog.ui
deactivate
