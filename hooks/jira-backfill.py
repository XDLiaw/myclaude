#!/usr/bin/env python3
"""
Claude Code PostToolUse hook: 把 commit / MR 連結自動補到對應的 JIRA 單。

用法（由 settings.json 的 hook 呼叫，hook JSON 從 stdin 進來）：
  python jira-backfill.py commit   # 在 `git commit`（Bash tool）之後
  python jira-backfill.py mr       # 在 GitLab create_merge_request MCP tool 之後
  python jira-backfill.py --ping       # 驗證 token / 網路 / 認證（唯讀，不寫票）
  python jira-backfill.py --selftest   # 離線自我測試（不碰 git / 網路）

行為：從 commit 訊息 / MR 標題抽出 JIRA 單號（預設專案 JKO、INCIDENT），
在該 JIRA 單上新增一則「留言」（comment，ADF 格式，內含可點的連結）。
去重：貼之前先查該單最近 50 則留言，若已有相同連結就跳過（避免同一 commit 被貼多次）。
除錯：每次觸發會 append 一行到 ~/.claude/hooks/jira-backfill.log。

設定（皆為環境變數，非硬編碼機密）：
  JIRA_API_TOKEN     Atlassian API token（必填，沒設就靜默略過）
  JIRA_EMAIL         Atlassian 帳號 email（預設 eric.liao@jkos.com）
  JIRA_BASE_URL      JIRA 站台（預設 https://jkopay.atlassian.net）
  JIRA_PROJECT_KEYS  要比對的專案 key，逗號分隔（預設 JKO,INCIDENT）

設計原則：永遠 exit 0，任何錯誤都不可中斷使用者的 session。
"""
import sys, os, json, re, base64, subprocess, datetime, urllib.request, urllib.error, urllib.parse

JIRA_BASE = os.environ.get("JIRA_BASE_URL", "https://jkopay.atlassian.net").rstrip("/")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "eric.liao@jkos.com")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
PROJECT_KEYS = [k.strip() for k in os.environ.get("JIRA_PROJECT_KEYS", "JKO,INCIDENT").split(",") if k.strip()]

KEY_RE = re.compile(r"\b(?:%s)-\d+\b" % "|".join(re.escape(k) for k in PROJECT_KEYS))
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jira-backfill.log")


def _log(msg):
    """append 一行除錯訊息到 log 檔（失敗也不影響主流程）。"""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass


def find_keys(text):
    """從文字抽出不重複的 JIRA 單號，保持出現順序。"""
    if not text:
        return []
    seen = []
    for m in KEY_RE.findall(text):
        if m not in seen:
            seen.append(m)
    return seen


def git(*args):
    try:
        # git 輸出為 UTF-8；明確指定 encoding，避免 Windows 預設 cp950 對中文
        # commit 訊息 decode 失敗（會讓 message 變空、抽不到單號）。
        return subprocess.check_output(
            ["git", *args], stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def remote_to_https(remote):
    """把 git remote URL 正規化成 https 的 repo base（去掉 .git）。
    支援 scp 式 git@host:group/proj.git 與 https://host/group/proj.git。"""
    if not remote:
        return ""
    r = remote.strip()
    m = re.match(r"git@([^:]+):(.+)", r)
    if m:
        r = "https://%s/%s" % (m.group(1), m.group(2))
    elif r.startswith("ssh://"):
        r = re.sub(r"^ssh://(?:git@)?", "https://", r)
    r = re.sub(r"\.git/?$", "", r)
    return r


def _first_json_str(blob, field):
    """從 JSON 文字裡抽出第一個 "field": "value" 的字串值（處理轉義）。抓不到回 ""。"""
    m = re.search(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % re.escape(field), blob or "")
    if not m:
        return ""
    try:
        return json.loads('"%s"' % m.group(1))
    except Exception:
        return m.group(1)


def _arg_value(cmd, flags):
    """從 shell 命令列抽出 -t/--title、-s/--source-branch 這類旗標的值。
    支援 "值"、'值'、=值、或空白分隔的裸值；抓不到回 ""。"""
    if not cmd:
        return ""
    for f in flags:
        m = re.search(r"(?:^|\s)%s(?:=|\s+)(\"([^\"]*)\"|'([^']*)'|(\S+))" % re.escape(f), cmd)
        if m:
            return m.group(2) or m.group(3) or m.group(4) or ""
    return ""


def mr_url_from_branch(branch):
    """Fallback：payload 沒帶 URL 時，用 GitLab API 依 source_branch 查 MR web_url。
    需要 GITLAB_TOKEN（或 GL_TOKEN）且 origin 為 GitLab；查不到回 ""。"""
    token = os.environ.get("GITLAB_TOKEN") or os.environ.get("GL_TOKEN", "")
    base = remote_to_https(git("remote", "get-url", "origin"))
    m = re.match(r"https?://([^/]+)/(.+)$", base)
    if not token or not branch or not m:
        return ""
    api = ("https://%s/api/v4/projects/%s/merge_requests?source_branch=%s"
           "&state=all&order_by=created_at&sort=desc"
           % (m.group(1), urllib.parse.quote(m.group(2), safe=""), urllib.parse.quote(branch, safe="")))
    req = urllib.request.Request(api, method="GET")
    req.add_header("PRIVATE-TOKEN", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            arr = json.load(resp)
        return arr[0].get("web_url", "") if arr else ""
    except Exception:
        return ""


def _auth_header():
    return "Basic " + base64.b64encode(("%s:%s" % (JIRA_EMAIL, JIRA_TOKEN)).encode()).decode()


def _url_in_comments(data, url):
    """純字串比對：URL 是否已出現在留言集合裡（去重判斷，可離線測試）。"""
    try:
        return url in json.dumps(data.get("comments", []), ensure_ascii=False)
    except Exception:
        return False


def comment_exists(key, url):
    """查該單最近 50 則留言是否已含此 URL。GET 失敗時回 False（寧可補、不漏）。"""
    if not JIRA_TOKEN:
        return False
    api = "%s/rest/api/3/issue/%s/comment?maxResults=50&orderBy=-created" % (JIRA_BASE, key)
    req = urllib.request.Request(api, method="GET")
    req.add_header("Authorization", _auth_header())
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return _url_in_comments(json.load(resp), url)
    except Exception:
        return False


def post_comment(key, label, url):
    """在 JIRA 單上新增一則留言（ADF），內含一段可點的連結文字。回傳 (成功?, 訊息)。"""
    if not JIRA_TOKEN:
        return (False, "no-token")
    api = "%s/rest/api/3/issue/%s/comment" % (JIRA_BASE, key)
    doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "\U0001f517 [Claude Code] "},
                    {"type": "text", "text": label[:250],
                     "marks": [{"type": "link", "attrs": {"href": url}}]},
                ],
            }
        ],
    }
    body = json.dumps({"body": doc}).encode("utf-8")
    req = urllib.request.Request(api, data=body, method="POST")
    req.add_header("Authorization", _auth_header())
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return (200 <= resp.status < 300, str(resp.status))
    except urllib.error.HTTPError as e:
        return (False, "HTTP %s" % e.code)
    except Exception as e:
        return (False, str(e))


def emit(msg):
    """在 Claude Code UI 顯示一行給使用者看。
    刻意用 ensure_ascii=True（\\uXXXX 轉義）輸出，避開 Windows/Git Bash
    stdout 非 UTF-8 造成的 UnicodeEncodeError；Claude Code 解析 JSON 時會還原。"""
    sys.stdout.write(json.dumps({"systemMessage": msg, "suppressOutput": True}) + "\n")


def link_all(keys, url, label):
    if not JIRA_TOKEN:
        emit("⚠️ 偵測到 %s 但未設定 JIRA_API_TOKEN，略過留言" % ", ".join(keys))
        _log("SKIP no-token keys=%s" % ",".join(keys))
        return
    done, dup, fail = [], [], []
    for k in keys:
        if comment_exists(k, url):
            dup.append(k)
            continue
        ok, info = post_comment(k, label, url)
        if ok:
            done.append(k)
        else:
            fail.append(k)
            _log("POST FAIL %s %s (%s)" % (k, url, info))
    parts = []
    if done:
        parts.append("✅ 已在 JIRA 留言（附連結）：%s" % ", ".join(done))
    if dup:
        parts.append("↩︎ 已有相同連結，略過：%s" % ", ".join(dup))
    if parts:
        emit("；".join(parts))
    _log("RESULT url=%s done=%s dup=%s fail=%s" % (url, done, dup, fail))


def handle_commit(data):
    ti = data.get("tool_input") or {}
    cmd = ti.get("command")
    if cmd is not None and "commit" not in cmd:  # 掛在 matcher=Bash 上，非 commit 指令略過
        return
    # 支援 `git -C <path> commit`：後續 git 查詢也要在同一 repo 目錄執行，
    # 否則 hook 的 cwd 若非該 repo，git log / rev-parse 會讀到錯的 repo（keys/sha 對不上）。
    gopts = ["-C", _arg_value(cmd, ["-C"])] if cmd and _arg_value(cmd, ["-C"]) else []
    msg = git(*gopts, "log", "-1", "--pretty=%B")
    sha = git(*gopts, "rev-parse", "HEAD")
    keys = find_keys(msg)
    _log("COMMIT keys=%s sha=%s gopts=%s" % (keys, sha[:8] if sha else None, gopts))
    if not keys or not sha:
        return
    base = remote_to_https(git(*gopts, "remote", "get-url", "origin"))
    url = "%s/-/commit/%s" % (base, sha) if base else sha
    subject = (msg.splitlines() or [""])[0][:120]
    link_all(keys, url, "commit %s — %s" % (sha[:8], subject))


def handle_mr(data):
    ti = data.get("tool_input") or {}
    tr = data.get("tool_response")
    tr_str = tr if isinstance(tr, str) else json.dumps(tr, ensure_ascii=False)

    # glab CLI（Bash tool）路徑：tool_input 只有 command，沒有 title/source_branch 欄位。
    # 自我把關：本 hook 掛在 matcher=Bash 上，非 `mr create` 的指令直接略過。
    cmd = ti.get("command")
    cli_title = cli_src = ""
    if cmd is not None:
        if "mr create" not in cmd:
            return
        cli_title = _arg_value(cmd, ["--title", "-t"])
        cli_src = _arg_value(cmd, ["--source-branch", "-s"])

    # 單號「只」從 title + source_branch 抽（不掃 description / target_branch，避免連坐其他單）
    title = ti.get("title") or cli_title or _first_json_str(tr_str, "title")
    src = ti.get("source_branch") or cli_src or _first_json_str(tr_str, "source_branch")
    keys = find_keys("%s %s" % (title, src))
    if not keys:  # payload 稀疏時退回當前 git branch（仍不碰 description/target）
        src = src or git("rev-parse", "--abbrev-ref", "HEAD")
        keys = find_keys(src)

    # URL：先取 web_url，再退 merge_requests 連結，最後用 GitLab API 依 branch 查
    url = _first_json_str(tr_str, "web_url")
    if not url:
        m = re.search(r"https?://[^\s\"']+/-/merge_requests/\d+", tr_str)
        url = m.group(0) if m else ""
    if not url:
        url = mr_url_from_branch(src)

    _log("MR keys=%s url=%s title=%r src=%r tr_head=%s" % (keys, url, title, src, tr_str[:400]))

    if not keys:
        _log("MR skip: no key in title/branch")
        return
    if not url:  # 抓不到連結不再靜默：出聲讓 Eric 手動補
        emit("⚠️ 偵測到 MR（%s）但抓不到 MR 連結，請手動補到 JIRA（或設 GITLAB_TOKEN 讓 hook 自動查）"
             % ", ".join(keys))
        return
    link_all(keys, url, "MR: %s" % (title[:120] if title else "merge request"))


def ping():
    """驗證 token / 網路 / 認證是否 OK（GET /myself，不寫任何票）。"""
    if not JIRA_TOKEN:
        print("JIRA_API_TOKEN not set")
        return
    req = urllib.request.Request(JIRA_BASE + "/rest/api/3/myself", method="GET")
    req.add_header("Authorization", _auth_header())
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            me = json.load(resp)
            print("OK: authenticated as %s (%s); base=%s; projects=%s"
                  % (me.get("displayName"), me.get("emailAddress"), JIRA_BASE, ",".join(PROJECT_KEYS)))
    except urllib.error.HTTPError as e:
        print("AUTH FAILED: HTTP %s (check JIRA_EMAIL / JIRA_API_TOKEN)" % e.code)
    except Exception as e:
        print("CONNECTION FAILED: %s" % e)


def selftest():
    assert find_keys("[JKO-28745] fix: remove ACCEPT check") == ["JKO-28745"]
    assert find_keys("no ticket here") == []
    assert find_keys("JKO-1 / INCIDENT-34 / JKO-1") == ["JKO-1", "INCIDENT-34"]
    assert find_keys("UTF-8 and SHA-1 are not keys") == []
    assert remote_to_https("git@gitlab.jkopay.app:rd3/insurance-api.git") == "https://gitlab.jkopay.app/rd3/insurance-api"
    assert remote_to_https("https://gitlab.jkopay.app/rd3/sub/insurance-api.git") == "https://gitlab.jkopay.app/rd3/sub/insurance-api"
    assert remote_to_https("") == ""
    u = "https://gitlab.jkopay.app/rd3/x/-/commit/abc123"
    assert _url_in_comments({"comments": [{"body": {"content": [{"content": [{"marks": [{"attrs": {"href": u}}]}]}]}}]}, u) is True
    assert _url_in_comments({"comments": []}, u) is False
    assert _url_in_comments({}, u) is False
    # _first_json_str：抽指定欄位字串
    assert _first_json_str('{"title":"[JKO-1] x","web_url":"https://h/-/merge_requests/9"}', "web_url") == "https://h/-/merge_requests/9"
    assert _first_json_str('{"a":"b"}', "title") == ""
    # 單號只從 title + source_branch 抽；description/target 的其他單號不連坐（模擬 MR !1753）
    mr_title = "[JKO-31533] feat: wire MTCH medical fee into CommonAlertJob"
    mr_src = "feature/JKO-31533-mtch-alert"
    assert find_keys("%s %s" % (mr_title, mr_src)) == ["JKO-31533"]
    assert find_keys("feature/JKO-31238-mtch Epic JKO-31238 reuse JKO-31531") == ["JKO-31238", "JKO-31531"]
    # _arg_value + glab CLI 路徑：從命令列抽 title / source-branch，再抽單號
    _cli = ('"C:/x/glab.exe" mr create -s feat/JKO-32984-remove-fastjson -b master '
            '-t "[JKO-32984] chore: 移除未使用的 fastjson 依賴 (RCE 漏洞清理)" -d "x"')
    assert _arg_value(_cli, ["--title", "-t"]) == "[JKO-32984] chore: 移除未使用的 fastjson 依賴 (RCE 漏洞清理)"
    assert _arg_value(_cli, ["--source-branch", "-s"]) == "feat/JKO-32984-remove-fastjson"
    assert find_keys("%s %s" % (_arg_value(_cli, ["--title", "-t"]), _arg_value(_cli, ["--source-branch", "-s"]))) == ["JKO-32984"]
    assert _arg_value("echo hi", ["-t"]) == ""
    # -C：支援 `git -C "<path>" commit` 抽出 repo 目錄
    assert _arg_value('git -C "C:/Workspace/x" commit -m "[JKO-1] y"', ["-C"]) == "C:/Workspace/x"
    assert _arg_value("git commit -m x", ["-C"]) == ""
    print("SELFTEST OK")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--selftest":
        selftest()
        return
    if mode == "--ping":
        ping()
        return
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    _log("FIRED mode=%s tool=%s" % (mode, (data or {}).get("tool_name")))
    try:
        if mode == "commit":
            handle_commit(data)
        elif mode == "mr":
            handle_mr(data)
    except Exception as e:
        _log("ERROR mode=%s %r" % (mode, e))  # 記錄但不中斷 session


if __name__ == "__main__":
    main()
