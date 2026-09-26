#!/bin/bash

source scripts/linux/create_venv.sh
source .venv/bin/activate
export PYTHONPATH=src/log_viewer
pytest -c tests/pytest.ini
TEST_RESULT=$?
deactivate
exit $TEST_RESULT
