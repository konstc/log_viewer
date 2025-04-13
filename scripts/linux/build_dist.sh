#!/bin/bash

rm -rf build
rm -rf dist

source scripts/linux/create_venv.sh
source .venv/bin/activate
pyinstaller --clean log_viewer.spec
VER=$(python src/log_viewer/version.py)
deactivate
                                                            
tar -czvf dist/log_viewer_${VER}.tar.gz dist/release
