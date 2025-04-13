#!/bin/bash

source scripts/linux/create_venv.sh
source .venv/bin/activate
python src/log_viewer/log_viewer.py
deactivate
