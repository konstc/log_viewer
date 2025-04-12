@setlocal
@echo off

rem This script should be executed from the root of the repository

set CUR_DIR=%cd%

call scripts\win\create_venv.bat

if exist "C:\Program files\7-Zip\7z.exe" (
    set ZIP="C:\Program files\7-Zip\"
) else (
    echo Please install 7zip into C:\Program files\7-Zip\
    exit /b 1
)

set PATH=%ZIP%;%PATH%

if exist build (
    rmdir /s /q build
)

if exist dist (
    rmdir /s /q dist
)

call .venv\Scripts\activate.bat
pyinstaller --clean log_viewer.spec
for /f "delims=" %%i in ('python src\log_viewer\version.py') do set VER=%%i
call .venv\Scripts\deactivate.bat

mkdir dist\release\cfg

copy cfg\app.json dist\release\cfg\app.json

%ZIP%\7z.exe a "%CUR_DIR%\dist\log_viewer_%VER%.zip" "%CUR_DIR%\dist\release" 

exit /b %ERRORLEVEL%

@endlocal
