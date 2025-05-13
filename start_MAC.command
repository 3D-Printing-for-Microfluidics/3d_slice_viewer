#!/usr/bin/env bash
# -------------------------------------------------------------
# Activate the venv and run main.py, mirroring Windows start.bat
# -------------------------------------------------------------
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"

python "$PROJECT_ROOT/main.py"
status=$?

if [[ $status -ne 0 ]]; then
  echo "⚠️  Python script encountered an error (exit code $status)."
  read -rp $'Press Enter to close…'
fi
