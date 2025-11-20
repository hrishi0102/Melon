#!/usr/bin/env bash
set -euo pipefail

echo "======================================"
echo "        Hardware Details"
echo "======================================"

# Run cross-platform hardware uuid script
./generate_hardware_uuid.sh

# -------------------------
# Config
# -------------------------
VENV_DIR="env"
REQ_FILE="requirements.txt"
PY_FILE="hardware_proof.py"

# Auto-detect python executable
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
elif command -v py &> /dev/null; then
    PYTHON_BIN="py"   # Windows py launcher
else
    echo "❌ Python not found."
    exit 1
fi

echo "[+] Using Python: $PYTHON_BIN"

# -------------------------
# Check virtualenv
# -------------------------
if [[ ! -d "$VENV_DIR" ]]; then
    echo "[+] Creating virtual environment: $VENV_DIR"
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Activate environment cross-platform
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32" ]]; then
    source "$VENV_DIR/Scripts/activate"
else
    source "$VENV_DIR/bin/activate"
fi

# Install requirements (if exist)
if [[ -f "$REQ_FILE" ]]; then
    echo "[+] Installing packages from $REQ_FILE..."
    pip install -r "$REQ_FILE"
fi

# -------------------------
# Run Python program
# -------------------------
echo "[+] Running $PY_FILE..."
$PYTHON_BIN "$PY_FILE"

echo "======================================"
echo "               DONE"
echo "======================================"
