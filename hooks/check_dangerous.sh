#!/bin/bash
# Claude Code PreToolUse Hook - 攔截危險 Bash 指令 & 敏感檔案存取
# 直接對原始 JSON 做 grep，不依賴 jq
input=$(cat)
set -f  # 關閉 glob 展開，避免 rm 目標含 * 時被 shell 意外展開

# === 敏感檔案路徑檢查（Read / Edit / Write / Grep / Glob） ===
# 從 file_path / path 欄位擷取路徑
# 注意：刻意不檢查 Grep 的 pattern 欄位（那是搜尋字串，會誤擋如搜尋 "credentials" 的程式碼）
file_path=$(echo "$input" | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | grep -oP ':\s*"\K[^"]*')
search_path=$(echo "$input" | grep -oP '"path"\s*:\s*"[^"]*"' | head -1 | grep -oP ':\s*"\K[^"]*')
check_target="${file_path}${search_path}"

if [ -n "$check_target" ]; then
  sensitive_patterns=(
    '\.env$'
    '\.env\.'
    '/secrets/'
    '\\secrets\\'
    '\.pem$'
    '\.key$'
    '/\.aws/'
    '\\\.aws\\'
    'credentials'
    'id_rsa'
    'id_ed25519'
  )
  for pattern in "${sensitive_patterns[@]}"; do
    if echo "$check_target" | grep -qiE "$pattern"; then
      echo "❌ 已攔截敏感檔案存取" >&2
      echo "   Path    : $check_target" >&2
      echo "   Pattern : $pattern" >&2
      exit 2
    fi
  done
fi

# === 以下為 Bash 指令檢查 ===
# 如果不是 Bash 工具（沒有 command 欄位），直接放行
if ! echo "$input" | grep -qP '"command"\s*:'; then
  exit 0
fi

# 擷取 command 字串並還原 JSON 跳脫；之後只比對指令本身，
# 不再 grep 整包 JSON（避免 description / 路徑等欄位造成誤判）
cmd=$(echo "$input" | grep -oP '"command"\s*:\s*"\K(\\.|[^"\\])*')
cmd=${cmd//\\\//\/}
cmd=${cmd//\\\"/\"}
cmd=${cmd//\\\\/\\}

dangerous_patterns=(
  # Git - 破壞性操作（git commit/push 改由 settings 的 ask 清單，跳原生確認框）
  "git reset --hard"
  "git clean -f"
  "git branch -D"
  "git branch -d "
  "git stash drop"
  "git stash clear"
  # Docker - 刪除 container/image
  "docker rm "
  "docker rmi "
  "docker container rm"
  "docker image rm"
  # Docker - 刪除 volume（資料遺失）
  "docker volume rm"
  "docker volume prune"
  # Docker - prune（清除未使用資源）
  "docker system prune"
  "docker image prune"
  "docker container prune"
  # 檔案刪除（rm 的細粒度規則在下方單獨處理；del 為 Windows cmd）
  "(^|[[:space:];&|])del[[:space:]]"
  "rd /s"
  # 檔案 in-place 修改
  "sed -i"
  # 檔案權限危險設定
  "chmod -R"
  "chmod 777"
  "chmod 666"
  # 磁碟寫入（dd of= 才是危險的）
  "dd of="
  # Windows 服務控制
  "sc start"
  "sc stop"
  "sc delete"
  "sc create"
  # Windows 工作排程
  "schtasks /create"
  "schtasks /delete"
  "schtasks /run"
  # Windows Registry（reg query 為唯讀，不在此清單）
  "reg add"
  "reg delete"
  "reg import"
  # Windows 系統
  "shutdown"
  "taskkill"
  "diskpart"
  "bcdedit"
  "net user"
  "net localgroup"
  # Linux/Mac - 提權（sudo 本身即為高風險操作）
  "sudo "
  # Linux/Mac - 系統服務
  "systemctl enable"
  "systemctl disable"
  "systemctl stop"
  "systemctl mask"
  "service stop"
  # Linux/Mac - 套件移除
  "apt remove"
  "apt purge"
  "apt-get remove"
  "apt-get purge"
  "yum remove"
  "dnf remove"
  "brew uninstall"
  # Linux/Mac - 使用者管理
  "useradd"
  "userdel"
  "usermod"
  "(^|[[:space:];&|])passwd([[:space:]]|$)"
  "groupdel"
  # 跨平台 - 排程
  "crontab"
)

for pattern in "${dangerous_patterns[@]}"; do
  if printf '%s' "$cmd" | grep -qE "$pattern"; then
    echo "❌ 已攔截危險指令，請確認後再執行" >&2
    echo "   Pattern : $pattern" >&2
    exit 2
  fi
done

# === git commit/push 不可與其他指令串接 ===
# 串接（cd x && git commit、git commit && git push 等）會繞過 settings 的 ask 確認規則
# （規則僅比對指令開頭），故擋下，要求拆成獨立指令再執行。
# 先移除引號內容再判斷，避免 commit 訊息中的 ; & | 造成誤判（如 git commit -m "fix; bug"）。
dq=$(printf '%s' "$cmd" | sed -e 's/"[^"]*"//g' -e "s/'[^']*'//g")
if printf '%s' "$dq" | grep -qE 'git[[:space:]]+(commit|push)\b'; then
  if printf '%s' "$dq" | grep -qE '&&|\|\||;|\|'; then
    echo "❌ 已攔截：git commit / git push 不可與其他指令串接（&&、||、;、| 等）" >&2
    echo "   原因：串接會繞過 commit/push 的確認流程。" >&2
    echo "   請改為分開、獨立執行：先單獨跑前置指令（如 cd、git add），" >&2
    echo "   再單獨執行 git commit 或 git push，然後重試。" >&2
    exit 2
  fi
fi

# === rm 規則：僅允許刪除 git 專案（work tree）內的檔案，專案外一律攔截 ===
# 目的：在有 git 保護的專案內可自由刪除（救得回）；非專案/系統檔案刪除無法復原，故擋下
if printf '%s' "$cmd" | grep -qE '(^|[^a-zA-Z])rm([^a-zA-Z]|$)'; then
  # 有效工作目錄：優先用 hook 傳入的 cwd；若指令以 "cd DIR &&" 開頭則改用該目錄
  eff_cwd=$(echo "$input" | grep -oP '"cwd"\s*:\s*"\K(\\.|[^"\\])*')
  eff_cwd=${eff_cwd//\\\\/\\}
  cd_dir=$(printf '%s' "$cmd" | grep -oP '^\s*cd\s+\K[^&;|]+' | head -1)
  [ -n "$cd_dir" ] && eff_cwd="$cd_dir"
  eff_cwd=$(printf '%s' "$eff_cwd" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'\'']//' -e 's/["'\'']$//')
  if command -v cygpath >/dev/null 2>&1 && [ -n "$eff_cwd" ]; then
    eff_cwd=$(cygpath -u "$eff_cwd" 2>/dev/null || printf '%s' "$eff_cwd")
  fi
  [ -z "$eff_cwd" ] && eff_cwd="$PWD"

  # 取最後一段 rm 之後、到下一個 shell 分隔符（; & |）為止的參數
  rm_args=$(printf '%s' "$cmd" | grep -oP '(^|[;&|])\s*rm\s+\K[^;&|]*' | tail -1)

  for tok in $rm_args; do
    case "$tok" in -*) continue ;; esac            # 略過 flag
    tok=$(printf '%s' "$tok" | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
    [ -z "$tok" ] && continue
    # Windows 絕對路徑（C:\... 或 C:/...）轉 POSIX
    case "$tok" in
      [A-Za-z]:[\\/]*) command -v cygpath >/dev/null 2>&1 && tok=$(cygpath -u "$tok" 2>/dev/null || printf '%s' "$tok") ;;
    esac
    # 解析成絕對路徑（相對路徑 → 接在 eff_cwd 後）
    case "$tok" in
      /*) abs="$tok" ;;
      *)  abs="$eff_cwd/$tok" ;;
    esac
    # realpath -m 會正規化 .. 等跳脫；非存在路徑也可解析
    abs=$(realpath -m "$abs" 2>/dev/null || printf '%s' "$abs")
    # 直接問 git：該目標所在目錄是否在 work tree 內（避開 git/realpath 路徑格式不一致）
    pdir=$(dirname "$abs")
    inside=$(git -C "$pdir" rev-parse --is-inside-work-tree 2>/dev/null)
    if [ "$inside" != "true" ]; then
      echo "❌ 已攔截危險指令：rm 目標不在 git 專案內，刪除後無法復原" >&2
      echo "   Target : $tok" >&2
      exit 2
    fi
  done
  # 所有目標皆在 git 專案內 → 放行
fi

exit 0
