import sys, json, subprocess, io
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

data = json.loads(sys.stdin.read())

# --- Model ---
model = data.get('model', {}).get('display_name', '?')

# --- Context ---
pct = data.get('context_window', {}).get('used_percentage') or 0

# --- Session ---
session_id = data.get('session_id', '')
session_name = data.get('session_name', '')
session_str = f'{session_id}({session_name})' if session_name else session_id

# --- CWD & Git Branch ---
cwd = data.get('cwd', '') or data.get('workspace', {}).get('current_dir', '')
branch = ''
if cwd:
    try:
        r = subprocess.run(['git', '-C', cwd, 'branch', '--show-current'],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=3)
        if r.returncode == 0:
            branch = r.stdout.strip()
    except Exception:
        pass

# --- 5h rate limit warning ---
rl5 = data.get('rate_limits', {}).get('five_hour')
rl5_pct = rl5.get('used_percentage', 0) if rl5 else 0
rl5_warn = ''
if rl5_pct >= 90:
    rl5_warn = f'  \U0001F6A8 5h {rl5_pct}%'
elif rl5_pct >= 80:
    rl5_warn = f'  \u26A0\uFE0F 5h {rl5_pct}%'

# --- Output ---
# Line 1: model  context usage  [5h warning]
line1 = f'{model}  \U0001F4CA {pct}% context{rl5_warn}'

# Line 2: session
line2 = f'\U0001F3AF {session_str}'

# Line 3: folder icon + cwd, git icon + branch
line3_parts = []
if cwd:
    line3_parts.append(f'\U0001F4C2 {cwd}')
if branch:
    line3_parts.append(f'\U0001F500 {branch}')
line3 = '  '.join(line3_parts)

print(line1)
print(line2)
print(line3)
