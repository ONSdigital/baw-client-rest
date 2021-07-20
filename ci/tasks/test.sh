#!/bin/bash
set -euo pipefail
cd baw-client-rest
python -m venv v-env
source v-env/bin/activate
python -m pip install --upgrade pip

pip install pipenv
pipenv install --dev
pytest