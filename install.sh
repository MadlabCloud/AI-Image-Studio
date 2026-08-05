#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-all}"
PROJECT_ROOT="${2:-$PWD}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

install_cli() {
  if [ ! -d "$ROOT/.venv" ]; then "$PYTHON_BIN" -m venv "$ROOT/.venv"; fi
  "$ROOT/.venv/bin/python" -m pip install --upgrade pip
  "$ROOT/.venv/bin/python" -m pip install -e "$ROOT[mcp]"
  "$ROOT/.venv/bin/python" -m ai_image_studio.cli doctor
}

install_skills() {
  "$ROOT/adapters/install-skills.sh" "$1" "$PROJECT_ROOT"
}

case "$TARGET" in
  claude|codex|project-claude|project-codex) install_skills "$TARGET" ;;
  cli) install_cli ;;
  all) install_cli; install_skills claude; install_skills codex ;;
  *) echo "Usage: $0 claude|codex|project-claude|project-codex|cli|all [project_root]" >&2; exit 2 ;;
esac
