#!/bin/bash
# WIP Session Viewer - 快速顯示未完成工作紀錄
# Usage: bash ~/.claude/wip.sh [cwd]
# If cwd is provided, filter by that path. Otherwise show all.

WIP_DIR="$HOME/.claude/wip"
CWD="${1:-}"

if [ ! -d "$WIP_DIR" ]; then
  echo "目前沒有任何 WIP 紀錄（目錄不存在）"
  exit 0
fi

# Find WIP files sorted by date descending, search up to 30 files
FILES=$(ls -1 "$WIP_DIR"/*.md 2>/dev/null | sort -r | head -30)

if [ -z "$FILES" ]; then
  echo "目前沒有任何 WIP 紀錄"
  exit 0
fi

# Normalize path: backslash→slash, Git Bash /c/→c:/, lowercase
normalize_path() {
  echo "$1" | sed 's|\\|/|g' | sed 's|^/\([a-zA-Z]\)/|\1:/|' | tr '[:upper:]' '[:lower:]'
}

# Check if record matches CWD (bidirectional prefix match)
# Bidirectional: cwd 在子目錄也能匹配父專案紀錄，反之亦然
matches_cwd() {
  local record="$1"
  local record_path
  record_path=$(echo "$record" | sed -n 's/.*\*\*專案路徑:\*\* `\([^`]*\)`.*/\1/p')
  local norm_cwd norm_record
  norm_cwd=$(normalize_path "$CWD")
  norm_record=$(normalize_path "$record_path")
  [[ "$norm_record" == "$norm_cwd"* ]] || [[ "$norm_cwd" == "$norm_record"* ]]
}

# Output a matched record with sequential number
output_record() {
  local record="$1"
  FOUND=$((FOUND + 1))
  echo "=== [$FOUND] ==="
  echo "$record"
  echo ""
}

FOUND=0
for FILE in $FILES; do
  CURRENT_RECORD=""

  while IFS= read -r line || [ -n "$line" ]; do
    if [[ "$line" =~ ^##\ \[ ]]; then
      # Process previous record if exists
      if [ -n "$CURRENT_RECORD" ]; then
        if [ -z "$CWD" ] || matches_cwd "$CURRENT_RECORD"; then
          output_record "$CURRENT_RECORD"
        fi
      fi
      CURRENT_RECORD="$line"
    elif [ -n "$CURRENT_RECORD" ]; then
      CURRENT_RECORD="$CURRENT_RECORD
$line"
    fi
  done < "$FILE"

  # Process last record in file
  if [ -n "$CURRENT_RECORD" ]; then
    if [ -z "$CWD" ] || matches_cwd "$CURRENT_RECORD"; then
      output_record "$CURRENT_RECORD"
    fi
  fi
done

if [ "$FOUND" -eq 0 ]; then
  if [ -n "$CWD" ]; then
    echo "此專案（$CWD）無未完成紀錄"
    echo "提示：不帶參數執行可查看全部專案紀錄"
  else
    echo "目前沒有任何 WIP 紀錄"
  fi
fi
