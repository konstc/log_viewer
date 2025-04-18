#!/bin/bash

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    if [ "$1" == "dist" ]; then
        pip install -r requirements_dist.txt
    else
        pip install -r requirements.txt
    fi
    deactivate
    echo Python virtual environment is created in .venv
else
    echo Python virtual environment already exists
fi
