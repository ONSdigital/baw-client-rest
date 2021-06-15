#!/bin/bash
set -euo pipefail
python -m pip install --upgrade pip
python -m venv v-env
source v-env/bin/activate
pip install pipenv
pipenv install --dev
pylint baw_client_rest