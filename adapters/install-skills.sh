#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-}"
PROJECT_ROOT="${2:-$PWD}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$TARGET" in
  claude) DEST="$HOME/.claude/skills" ;;
  codex) DEST="$HOME/.agents/skills" ;;
  project-claude) DEST="$PROJECT_ROOT/.claude/skills" ;;
  project-codex) DEST="$PROJECT_ROOT/.agents/skills" ;;
  *) echo "Usage: $0 claude|codex|project-claude|project-codex [project_root]" >&2; exit 2 ;;
esac
mkdir -p "$DEST"
for d in "$ROOT"/skills/*; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  rm -rf "$DEST/$name"
  cp -R "$d" "$DEST/$name"
done
echo "Skills installed in $DEST"
