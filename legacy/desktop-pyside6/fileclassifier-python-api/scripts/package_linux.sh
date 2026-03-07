#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-onedir}"
if [[ "$MODE" != "onedir" && "$MODE" != "onefile" ]]; then
  echo "Usage: bash ./scripts/package_linux.sh [onedir|onefile]" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
APP_NAME="FileClassifier"

if [[ ! -x "$VENV_PYTHON" ]]; then
  python3 -m venv "$PROJECT_ROOT/.venv"
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -e "$PROJECT_ROOT"
fi

HAS_PYINSTALLER="$("$VENV_PYTHON" -c "import importlib.util; print('1' if importlib.util.find_spec('PyInstaller') else '0')")"
if [[ "$HAS_PYINSTALLER" != "1" ]]; then
  "$VENV_PYTHON" -m pip install "pyinstaller>=6.13,<7"
fi

BUILD_ARGS=(
  -m PyInstaller
  --noconfirm
  --clean
  --windowed
  --name "$APP_NAME"
  --distpath "$PROJECT_ROOT/dist"
  --workpath "$PROJECT_ROOT/build"
  --specpath "$PROJECT_ROOT"
  --paths "$PROJECT_ROOT/src"
  --add-data "data/sample_records.xlsx:data"
  --add-data "src/fileclassifier/assets:assets"
)

if [[ "$MODE" == "onefile" ]]; then
  BUILD_ARGS+=(--onefile)
fi

BUILD_ARGS+=("$PROJECT_ROOT/src/fileclassifier/main.py")
"$VENV_PYTHON" "${BUILD_ARGS[@]}"

if [[ "$MODE" == "onefile" ]]; then
  BIN_PATH="$PROJECT_ROOT/dist/$APP_NAME"
else
  BIN_PATH="$PROJECT_ROOT/dist/$APP_NAME/$APP_NAME"
fi

if [[ ! -e "$BIN_PATH" ]]; then
  echo "Build finished but executable not found: $BIN_PATH" >&2
  exit 1
fi

echo
echo "Build succeeded."
echo "Run executable:"
echo "$BIN_PATH"
