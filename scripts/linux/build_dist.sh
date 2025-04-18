#!/bin/bash

rm -rf build
rm -rf dist

source scripts/linux/create_venv.sh dist
source .venv/bin/activate
pyinstaller --clean log_viewer.spec
ARCH=$(uname -m)
deactivate
                                                            
tar -czvf dist/log_viewer-linux-${ARCH}.tar.gz dist/release
