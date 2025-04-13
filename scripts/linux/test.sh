#!/bin/bash

source scripts/linux/create_venv.sh
source .venv/bin/activate
export PYTHONPATH=src/log_viewer
pytest
deactivate
