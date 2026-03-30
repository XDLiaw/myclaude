#!/bin/bash
PY=$(command -v python 2>/dev/null || command -v python3 2>/dev/null)

if [ -z "$PY" ]; then
  echo "[no python found]"
  exit 0
fi

"$PY" -X utf8 ~/.claude/statusline.py 2>&1 || echo "[statusline script error]"
