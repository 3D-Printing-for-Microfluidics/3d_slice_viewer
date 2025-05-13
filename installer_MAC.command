#!/usr/bin/env bash
# -------------------------------------------------------------
# Create a local virtual-env and pip-install `requirements.txt`
# -------------------------------------------------------------
set -euo pipefail

# ── locate repo root ─────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ── make sure we have Python (≥3.10) ─────────────────────────
if ! command -v python3 >/dev/null 2>&1 ; then
  echo "❌  python3 not found.  Install Xcode CLT or Homebrew Python first."
  exit 1
fi

# ── create or recreate the venv ──────────────────────────────
VENV_DIR="$PROJECT_ROOT/venv"
if [[ "${1:-}" == "--reset" ]]; then rm -rf "$VENV_DIR"; fi
if [[ ! -d "$VENV_DIR" ]]; then
  echo "📦  Creating virtual environment in ./venv ..."
  python3 -m venv "$VENV_DIR"
fi

# ── activate & install deps ──────────────────────────────────
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel
pip install -r "$PROJECT_ROOT/requirements.txt"
deactivate

echo "✅  Setup complete.  Run ./MACstart.command to launch the app."
