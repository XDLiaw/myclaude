#!/bin/bash
# Claude Code PreToolUse Hook - 攔截危險 Bash 指令 & 敏感檔案存取
# 直接對原始 JSON 做 grep，不依賴 jq
input=$(cat)

# === 敏感檔案路徑檢查（Read / Edit / Write / Grep / Glob） ===
# 從 file_path / path / pattern 欄位擷取路徑
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

dangerous_patterns=(
  # Git - 破壞性操作（git commit/push 已移至 deny list，由原生對話框處理）
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
  # 檔案刪除（rm 的細粒度規則在下方單獨處理）
  "del "
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
  # Windows Registry
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
  # PowerShell（Windows）
  "powershell"
  "pwsh"
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
  "passwd"
  "groupdel"
  # 跨平台 - 排程
  "crontab"
)

for pattern in "${dangerous_patterns[@]}"; do
  if echo "$input" | grep -qE "$pattern"; then
    echo "❌ 已攔截危險指令，請確認後再執行" >&2
    echo "   Pattern : $pattern" >&2
    exit 2
  fi
done

# rm 細粒度規則：允許刪除當前目錄下的相對路徑檔案，攔截高風險操作
if echo "$input" | grep -qE '\brm\b'; then
  # 攔截：遞迴刪除 (-r, -rf, -fr)
  if echo "$input" | grep -qE 'rm\s+(-[a-z]*r|-rf|-fr)'; then
    echo "❌ 已攔截危險指令：rm 遞迴刪除" >&2
    exit 2
  fi
  # 攔截：刪除絕對路徑 (rm /path 或 rm -f /path)
  if echo "$input" | grep -qE 'rm\s+(-[a-z]+\s+)?/'; then
    echo "❌ 已攔截危險指令：rm 絕對路徑" >&2
    exit 2
  fi
  # 攔截：路徑跳脫 (..)
  if echo "$input" | grep -qE 'rm\s.*\.\.'; then
    echo "❌ 已攔截危險指令：rm 包含 .. 路徑跳脫" >&2
    exit 2
  fi
  # 攔截：萬用字元刪除 (rm *, rm -f *)
  if echo "$input" | grep -qE 'rm\s+(-[a-z]+\s+)?\*'; then
    echo "❌ 已攔截危險指令：rm 萬用字元" >&2
    exit 2
  fi
  # 其餘 rm（相對路徑指定檔案）→ 放行
fi

exit 0
