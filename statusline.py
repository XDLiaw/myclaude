import sys, json, re, subprocess

raw = sys.stdin.read()

# Extract values with regex - no full JSON parsing needed
m = re.search(r'"display_name"\s*:\s*"([^"]*)"', raw)
model = m.group(1) if m else '?'

m = re.search(r'"cwd"\s*:\s*"(.*?)"', raw)
cwd_raw = m.group(1) if m else ''
# Use json.loads to properly unescape JSON string (handles \\ -> \ correctly)
try:
    cwd = json.loads('"' + cwd_raw + '"')
except Exception:
    cwd = cwd_raw.replace('\\\\', '\\')

m = re.search(r'"used_percentage"\s*:\s*(\d+)', raw)
pct = m.group(1) if m else '0'

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

if branch:
    print(f'[{model}] {cwd} ({branch}) | {pct}% context')
else:
    print(f'[{model}] {cwd} | {pct}% context')
