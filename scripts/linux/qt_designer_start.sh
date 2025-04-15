#!/bin/bash

source scripts/linux/create_venv.sh
source .venv/bin/activate
pyqt6-tools designer
deactivate
