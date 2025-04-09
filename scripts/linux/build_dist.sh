#!/bin/bash
rm -rf build
rm -rf dist

source .venv/bin/activate
pyinstaller --clean log_viewer.spec
VER=$(python src/log_viewer/version.py)
deactivate

mkdir dist/release/cfg
cp cfg/app.json dist/release/cfg/app.json
tar -czvf dist/log_viewer_${VER}.tar.gz dist/release
