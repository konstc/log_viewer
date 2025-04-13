#!/bin/bash

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    deactivate
    echo Python virtual environment is created in .venv
else
    echo Python virtual environment already exists
fi
