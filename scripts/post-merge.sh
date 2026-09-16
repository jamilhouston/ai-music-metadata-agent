#!/usr/bin/env bash
set -euo pipefail

python -m pip install --break-system-packages --disable-pip-version-check --no-input -r requirements.txt
python -m compileall -q app.py music_metadata tests