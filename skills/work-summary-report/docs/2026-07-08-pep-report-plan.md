# PEP 自評報告功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 為 `work-summary-report` skill 新增 PEP 期中績效自評報告產出能力，並實際產出 Eric 的 2026H1 PEP 自評 HTML。

**Architecture:** 方案 A — 獨立產生器 `build_pep_report.py` 與既有 `build_report.py` 並存、共讀同一份 `data/`；J3 指標目錄放在單一真相來源 `pep_catalog.py`；可 curate 的佐證映射放在 `pep_mapping.json`；先自動起草再由 Eric 篩選。全部收進 skill 底下 `reports/2026H1/`。

**Tech Stack:** Python 3（標準庫 `json`/`html`/`re`）、自包含 HTML/CSS/JS（沿用 `assets/build_report_example.py` 藍本）。

**環境備註（重要）：**
- 本目錄**不是 git repo**，且依 Eric 全域規則**不主動 commit**。故本計畫以「檢查點：驗證」取代所有 commit 步驟。
- Windows + Git Bash。跑會印中文的 Python 前先 `export PYTHONIOENCODING=utf-8`。
- 所有寫檔 UTF-8；JSON `ensure_ascii=False`。
- 路徑一律絕對路徑。`BASE = C:/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1`。

**與 spec 的一處精化：** spec 的 `pep_mapping.json` 範例在每個 indicator 放了 `text`。實作改為 **indicator 文字放在 `pep_catalog.py`（單一真相來源），`pep_mapping.json` 只帶 `evidence`**，避免文字重複與不一致。功能等價，schema 更乾淨。

---

## File Structure

```
~/.claude/skills/work-summary-report/reports/2026H1/
├── data/                       # 既有（遷移）：jira_h1_2026.json / completed_h1_keys.json / rd3_weekly_part1~4.md
├── build_report.py             # 既有（遷移）：工作總整理產生器，BASE 改指到此
├── Eric_2026H1_已完成工作總整理.html   # 既有（遷移，重跑後產物）
├── pep_catalog.py              # 新增：J3 指標目錄 + 核心價值（單一真相來源）
├── pep_mapping.json            # 新增：可 curate 的佐證映射（先自動起草）
├── validate_mapping.py         # 新增：pep_mapping.json 結構/鍵值驗證器
├── build_pep_report.py         # 新增：PEP 報告產生器
└── Eric_2026H1_PEP自評.html     # 新增：產物
```

各檔責任：
- `pep_catalog.py`：純資料模組，定義六職能與各指標文字、核心價值順序。被 generator 與 validator 共用。
- `pep_mapping.json`：Eric 的實際佐證資料（哪些單對到哪個指標、案例句、工作項目、核心價值事蹟、Top Two Wins 候選）。
- `validate_mapping.py`：獨立驗證器，確保 mapping 結構正確、所有佐證 key ∈ 152 完成單。
- `build_pep_report.py`：讀 catalog + mapping + jira 原始資料 → 產 HTML。

---

## Task 0: 建立資料夾並遷移 2026H1（複製，不刪舊）

**Files:**
- Create dir: `C:/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1/`
- Copy from: `C:/Users/eric.liao/Documents/2026H1-工作總整理/*`
- Modify: `reports/2026H1/build_report.py`（`BASE` 一行）

- [ ] **Step 1: 建立資料夾並複製既有內容（保留舊資料夾當備份）**

Run:
```bash
mkdir -p "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
cp -r "/c/Users/eric.liao/Documents/2026H1-工作總整理/." "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1/"
ls -R "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
```
Expected: 新資料夾含 `build_report.py`、`Eric_2026H1_已完成工作總整理.html`、`data/`（4 個 md + 2 個 json）。舊 `Documents/2026H1-工作總整理/` **原封不動保留**。

- [ ] **Step 2: 更新遷移後 build_report.py 的 BASE**

Modify `reports/2026H1/build_report.py` 第一個 `BASE = ...` 行：
```python
BASE = r"C:/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
```

- [ ] **Step 3: 重跑既有產生器，確認工作總整理仍正常**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python build_report.py
```
Expected: 印出 `completed-in-H1: 152 | ... | by_area: {...}`，且 `HTML written: <大於 90000> chars`。與遷移前一致（152 張）。

- [ ] **Step 4: 檢查點 — 驗證遷移**

Run:
```bash
ls -la "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1/Eric_2026H1_已完成工作總整理.html"
```
Expected: HTML 存在、mtime 為剛剛。舊資料夾保留為備份（Task 8 再問是否刪）。

---

## Task 1: `pep_catalog.py`（J3 指標目錄，單一真相來源）

**Files:**
- Create: `reports/2026H1/pep_catalog.py`

- [ ] **Step 1: 寫入指標目錄模組**

Create `reports/2026H1/pep_catalog.py`（來源：Confluence 1669660766 J3 PEP 標準）：
```python
# -*- coding: utf-8 -*-
"""J3 資深軟體工程師 PEP 指標目錄（單一真相來源）。
來源：https://jkopay.atlassian.net/wiki/spaces/Engineerin/pages/1669660766
generator 與 validator 共用；pep_mapping.json 只帶 evidence，不重複這裡的文字。"""

# comp_key -> (顯示名稱, {indicator_no: 指標文字})，dict 保序即呈現順序
CATALOG = {
    "technical": ("技術能力 Technical Excellence", {
        "1": "快速定位問題根源；線上問題能快速恢復穩定並提出事件總結與前後脈絡",
        "2": "前瞻性分析技術方案優劣，提前識別風險並提出架構調整建議",
        "3": "中大型專案的技術統整與決策，掌握專案全局",
        "4": "核心任務中擔任任務梳理與協調實作同仁的角色",
        "5": "跨多個技術領域（Coding、CI/CD、基礎設施）",
        "6": "準確同步資訊給利害關係人，遇阻擋迅速反映不卡在自己手上",
        "7": "Code Review 提供建設性意見，有效協助成員解決問題、提升能力",
    }),
    "leadership": ("領導力與影響力 Leadership & Influence", {
        "1": "指導初階工程師（Code Review、Pair Programming、即時回饋）",
        "2": "協助成員設定成長方向，並創造練習與成長的機會",
        "3": "依團隊能力與分工，規劃適合成員能力的執行計畫",
        "4": "以不同角度（業務、技術、分析）提出建設性回饋",
        "5": "技術方案討論中協助團隊收斂出可執行方向",
    }),
    "delivery": ("交付與當責 Delivery & Accountability", {
        "1": "提出可行計畫、在預定時間內達成業務目標，且對品質有高標準",
        "2": "給定目標後能獨立評估研究並歸納出解決方案",
        "3": "執行前主動即時提出專案風險，確保如期上線",
        "4": "主動承擔責任，對負責領域看到問題就動手",
        "5": "上線後有足夠監控指標與告警，讓系統穩定運行",
    }),
    "communication": ("溝通與協作 Communication & Collaboration", {
        "1": "與不同團隊協調相依的工作事項與交付時間",
        "2": "主動提出高可行意見，快速分解工作並分配任務",
        "3": "在會議或多人討論中整理出關鍵重點，確保理解一致",
        "4": "主持/帶領會議有明確的摘要與進程（決定了什麼、誰負責什麼）",
    }),
    "business": ("業務與策略 Business & Strategy", {
        "1": "持續分享專業知識經驗，建立「遇到這類問題可以找我」的信任感",
        "2": "對負責業務範圍提出建設性建議與可行選項，而非只反映問題",
        "3": "熟悉並在團隊推廣、執行公司政策與方向",
        "4": "落實管理工具（Jira、Slack、Confluence）使用並協助同事執行政策",
    }),
    "ai": ("AI 素養與應用 AI Literacy & Application", {
        "1": "策略性應用：依任務特性選擇是否/如何使用 AI，並能舉出改善工作流程的具體案例",
        "2": "品質治理：Code Review 中以相同標準把關 AI 輔助產出，識別架構/安全/效能問題",
        "3": "團隊賦能：主動分享有效 AI 使用技巧，協助 J2 建立正確使用習慣",
        "4": "流程改善：推動將 AI 整合到團隊開發流程（review、測試補充、文件生成等）",
    }),
}

# core_value_key -> 顯示名稱（保序）
CORE_VALUES = [
    ("user_first", "先從用戶出發"),
    ("candor", "大膽坦率"),
    ("break_inertia", "跳脫慣性"),
    ("fast_and_accurate", "非常快儘量準"),
    ("all_in", "全心投入"),
]
```

- [ ] **Step 2: 驗證模組可載入且內容正確**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python -c "import pep_catalog as c; assert len(c.CATALOG)==6; assert sum(len(v[1]) for v in c.CATALOG.values())==29; assert len(c.CORE_VALUES)==5; print('catalog OK: 6 comps, 29 indicators, 5 core values')"
```
Expected: `catalog OK: 6 comps, 29 indicators, 5 core values`

---

## Task 2: `validate_mapping.py` + 空骨架 `pep_mapping.json`（TDD）

**Files:**
- Create: `reports/2026H1/validate_mapping.py`
- Create: `reports/2026H1/pep_mapping.json`

- [ ] **Step 1: 先寫驗證器（會先失敗，因為還沒有 mapping 檔）**

Create `reports/2026H1/validate_mapping.py`：
```python
# -*- coding: utf-8 -*-
"""驗證 pep_mapping.json：結構正確、職能/核心價值鍵齊全、所有佐證 key ∈ 152 完成單。"""
import json, sys
from pep_catalog import CATALOG, CORE_VALUES

BASE = r"C:/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
COMPLETED = set(json.load(open(BASE + "/data/completed_h1_keys.json", encoding="utf-8")))
MAP = json.load(open(BASE + "/pep_mapping.json", encoding="utf-8"))

errors, n_ev = [], 0

# top-level keys
for k in ("level", "period", "work_items", "competencies", "core_values", "top_two_wins"):
    if k not in MAP:
        errors.append(f"缺少頂層欄位: {k}")

# competencies 鍵需與 catalog 完全一致
if set(MAP.get("competencies", {}).keys()) != set(CATALOG.keys()):
    errors.append(f"competencies 鍵不符 catalog: {set(MAP.get('competencies',{}))} vs {set(CATALOG)}")

# 每個指標的 evidence.key 必須是完成單
for comp_key, (_, inds) in CATALOG.items():
    comp = MAP.get("competencies", {}).get(comp_key, {})
    for num, cell in comp.get("indicators", {}).items():
        if num not in inds:
            errors.append(f"{comp_key} 出現未知指標編號 #{num}")
        for e in cell.get("evidence", []):
            n_ev += 1
            if e.get("key") not in COMPLETED:
                errors.append(f"{comp_key}#{num} 佐證 {e.get('key')} 不在 152 完成單")
            if not (e.get("case") or "").strip():
                errors.append(f"{comp_key}#{num} 佐證 {e.get('key')} 缺 case 文字")

# core_values 鍵需齊全
cv_keys = {k for k, _ in CORE_VALUES}
if set(MAP.get("core_values", {}).keys()) != cv_keys:
    errors.append(f"core_values 鍵不符: {set(MAP.get('core_values',{}))} vs {cv_keys}")
for cvk, cell in MAP.get("core_values", {}).items():
    for c in cell.get("cases", []):
        if c.get("key") and c["key"] not in COMPLETED:
            errors.append(f"核心價值 {cvk} 佐證 {c['key']} 不在 152 完成單")

# top_two_wins
for i, t in enumerate(MAP.get("top_two_wins", [])):
    for f in ("title", "impact", "evidence"):
        if f not in t:
            errors.append(f"top_two_wins[{i}] 缺 {f}")
    for k in t.get("evidence", []):
        if k not in COMPLETED:
            errors.append(f"top_two_wins[{i}] 佐證 {k} 不在 152 完成單")

if errors:
    print("FAIL:", len(errors), "個問題")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"PASS: mapping 結構正確；共 {n_ev} 筆指標佐證、{len(MAP['top_two_wins'])} 件 Top Two Wins 候選")
```

- [ ] **Step 2: 執行驗證器，確認失敗（尚無 mapping 檔）**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python validate_mapping.py
```
Expected: FAIL，`FileNotFoundError: ... pep_mapping.json`（檔案還沒建）。

- [ ] **Step 3: 建立空骨架 mapping**

Create `reports/2026H1/pep_mapping.json`（六職能各帶空 indicators、五核心價值空 cases、空 work_items/top_two_wins）：
```json
{
  "level": "J3",
  "period": "2026H1",
  "work_items": [],
  "competencies": {
    "technical": { "indicators": {} },
    "leadership": { "indicators": {} },
    "delivery": { "indicators": {} },
    "communication": { "indicators": {} },
    "business": { "indicators": {} },
    "ai": { "indicators": {} }
  },
  "core_values": {
    "user_first": { "cases": [] },
    "candor": { "cases": [] },
    "break_inertia": { "cases": [] },
    "fast_and_accurate": { "cases": [] },
    "all_in": { "cases": [] }
  },
  "top_two_wins": []
}
```

- [ ] **Step 4: 執行驗證器，確認通過**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python validate_mapping.py
```
Expected: `PASS: mapping 結構正確；共 0 筆指標佐證、0 件 Top Two Wins 候選`

---

## Task 3: `build_pep_report.py` — 資料載入與 helper（先驗後實作）

**Files:**
- Create: `reports/2026H1/build_pep_report.py`
- Check: `reports/2026H1/_check_helpers.py`（暫時，Step 4 後刪）

- [ ] **Step 1: 寫 helper 檢查腳本（會先失敗）**

Create `reports/2026H1/_check_helpers.py`：
```python
# -*- coding: utf-8 -*-
import build_pep_report as b
# JKO-27897 = 調閱國壽 UAT 保單異常 Log（已在 152 完成單）
assert b.summary_of("JKO-27897"), "summary_of 應能查到 JKO-27897 摘要"
assert b.summary_of("NOPE-0") == "", "查不到應回空字串"
out = b.linkify_jko("見 JKO-27897 與 JKO-25558")
assert out.count('<a class="jko"') == 2, "應把兩個 JKO 轉連結"
assert 'href="https://jkopay.atlassian.net/browse/JKO-27897"' in out
print("helpers OK")
```

- [ ] **Step 2: 執行，確認失敗（模組還沒建）**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python _check_helpers.py
```
Expected: FAIL，`ModuleNotFoundError: No module named 'build_pep_report'`。

- [ ] **Step 3: 建立產生器的載入與 helper 區塊**

Create `reports/2026H1/build_pep_report.py`（本 Task 只到 helper；HTML 組裝在 Task 4 續補）：
```python
# -*- coding: utf-8 -*-
import json, html, re
from pep_catalog import CATALOG, CORE_VALUES

BASE = r"C:/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
JKO_BASE = "https://jkopay.atlassian.net/browse/"

alldata = json.load(open(BASE + "/data/jira_h1_2026.json", encoding="utf-8"))
JIRA = {r.get("key"): r for r in alldata}          # key -> 原始紀錄
MAP = json.load(open(BASE + "/pep_mapping.json", encoding="utf-8"))
COMPLETED = set(json.load(open(BASE + "/data/completed_h1_keys.json", encoding="utf-8")))

def esc(s):
    return html.escape(s or "")

def linkify_jko(text):
    return re.sub(r'JKO-\d+',
        lambda m: f'<a class="jko" href="{JKO_BASE}{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>',
        text)

def summary_of(key):
    r = JIRA.get(key)
    return r.get("summary") if r else ""
```

- [ ] **Step 4: 執行檢查通過後刪除暫時腳本**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python _check_helpers.py && rm _check_helpers.py && echo "helpers verified, temp removed"
```
Expected: `helpers OK` 然後 `helpers verified, temp removed`。

---

## Task 4: `build_pep_report.py` — HTML 段落組裝與產出（用骨架 mapping 驗證）

**Files:**
- Modify: `reports/2026H1/build_pep_report.py`（在 helper 之後追加）

- [ ] **Step 1: 追加段落建構、模板、寫檔與自我核對輸出**

在 `build_pep_report.py` 末端追加：
```python
# ---------- 段落一：工作項目 ----------
CAT_COLOR = {"業務專案": "#2563eb", "技術專案": "#16a34a", "其他": "#64748b"}
wi_html = ""
for w in MAP.get("work_items", []):
    col = CAT_COLOR.get(w.get("category"), "#64748b")
    chips = "".join(f'<span class="chip">{k}</span>' for k in w.get("keys", []))
    wi_html += (
        f'<div class="theme" style="border-left-color:{col}">'
        f'<h3>{esc(w.get("theme"))}<span class="thtag" style="color:{col};border-color:{col};background:{col}14">{esc(w.get("category"))}</span></h3>'
        f'<p style="margin:6px 0 0;font-size:14px;">{esc(w.get("desc"))}</p>'
        f'<div class="tickets">相關單：{chips}</div></div>'
    )
if not wi_html:
    wi_html = '<div class="nocase">（尚無工作項目）</div>'

# ---------- 段落二：PEP 標準自評（六職能） ----------
comp_html = ""
ind_covered = 0
for comp_key, (comp_name, indicators) in CATALOG.items():
    cells = MAP.get("competencies", {}).get(comp_key, {}).get("indicators", {})
    n_cases = sum(len(cells.get(num, {}).get("evidence", [])) for num in indicators)
    rows = ""
    for num, text in indicators.items():
        ev = cells.get(num, {}).get("evidence", [])
        if ev:
            ind_covered += 1
            lis = "".join(f'<li>{esc(e.get("case"))}（{e.get("key")}）</li>' for e in ev)
            body = f'<ul>{lis}</ul>'
        else:
            body = '<div class="nocase">（尚無案例）</div>'
        rows += f'<div class="ind"><div class="ind-h">#{num}「{esc(text)}」</div>{body}</div>'
    comp_html += (
        f'<details class="comp" open><summary>{esc(comp_name)}'
        f'<span class="cover">涵蓋 {n_cases} 筆佐證</span></summary>{rows}</details>'
    )

# ---------- 段落三：核心價值 ----------
cv_html = ""
for cv_key, cv_name in CORE_VALUES:
    cases = MAP.get("core_values", {}).get(cv_key, {}).get("cases", [])
    if cases:
        lis = "".join(
            f'<li>{esc(c.get("case"))}{("（"+c["key"]+"）") if c.get("key") else ""}</li>'
            for c in cases)
        body = f'<ul>{lis}</ul>'
    else:
        body = '<div class="nocase">（尚無案例）</div>'
    cv_html += f'<div class="cv"><div class="cv-h">{esc(cv_name)}</div>{body}</div>'

# ---------- Top Two Wins 候選 ----------
ttw_html = ""
for t in MAP.get("top_two_wins", []):
    chips = "".join(f'<span class="chip">{k}</span>' for k in t.get("evidence", []))
    ttw_html += (
        f'<div class="win"><div class="win-t">{esc(t.get("title"))}</div>'
        f'<div class="win-i">{esc(t.get("impact"))}</div>'
        f'<div class="tickets">{chips}</div></div>'
    )
if not ttw_html:
    ttw_html = '<div class="nocase">（尚無候選）</div>'

# ---------- KPI ----------
total_ind = sum(len(v[1]) for v in CATALOG.values())
n_cv_cases = sum(len(MAP.get("core_values", {}).get(k, {}).get("cases", [])) for k, _ in CORE_VALUES)
kpi = [
    ("152", "本期完成單", "完成時間落在 2026 H1"),
    (f"{ind_covered}/{total_ind}", "已對到指標", "六職能有佐證的指標數"),
    (str(n_cv_cases), "核心價值事蹟", "本人事蹟"),
    (str(len(MAP.get("top_two_wins", []))), "Top Two Wins 候選", "供回饋平台挑 1–2 件"),
]
kpi_html = "".join(
    f'<div class="kpi"><div class="kpi-num">{n}</div><div class="kpi-label">{l}</div><div class="kpi-sub">{s}</div></div>'
    for n, l, s in kpi)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eric Liao — 2026 上半年 PEP 自評素材</title>
<style>
__BASE_STYLE__
/* --- PEP 專屬 --- */
.kpis{grid-template-columns:repeat(4,1fr);}
details.comp{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;padding:4px 18px;box-shadow:0 2px 8px rgba(30,41,59,.04);}
details.comp>summary{cursor:pointer;font-size:16px;font-weight:700;padding:12px 0;display:flex;align-items:center;gap:10px;}
.ind{border-top:1px dashed var(--line);padding:10px 0;}
.ind-h{font-size:13.5px;font-weight:600;color:#334155;}
.ind ul{margin:6px 0 0;padding-left:20px;}
.ind li{font-size:14px;margin:4px 0;}
.nocase{color:var(--muted);font-size:12.5px;font-style:italic;padding:4px 0;}
.cv{background:var(--card);border:1px solid var(--line);border-left:4px solid #7c3aed;border-radius:0 12px 12px 0;padding:12px 18px;margin:10px 0;}
.cv-h{font-weight:700;font-size:15px;}
.win{background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:14px 18px;margin:10px 0;}
.win-t{font-weight:700;font-size:15px;color:#7c2d12;}
.win-i{font-size:13.5px;margin:4px 0;color:#7c2d12;}
</style>
</head>
<body>
<div class="wrap">
<header class="hero">
  <h1>2026 上半年 PEP 自評素材</h1>
  <div class="sub">Eric Liao ・ 技術部 RD3 ・ 對照職級：J3 資深軟體工程師 ・ 素材來源：JIRA (JKO) + RD3 週報</div>
  <div class="meta">
    <span><b>期間</b> 2026-01-01 ~ 2026-06-30</span>
    <span><b>用途</b> 填寫公司 PEP 文件 / Top Two Wins 之草稿素材</span>
    <span><b>注意</b> 自評草稿，請自行核實後採用</span>
  </div>
</header>

<section><div class="kpis">__KPI__</div></section>

<section>
  <h2><span class="bar"></span>Top Two Wins 候選</h2>
  <p class="section-note">聚焦「影響力」（另填在回饋平台，與 PEP 不同機制）。以下為候選，最終挑 1–2 件。</p>
  __TTW__
</section>

<section>
  <h2><span class="bar"></span>一、工作項目</h2>
  <p class="section-note">本期主要工作/專案（業務專案、技術專案、其他）。</p>
  __WORK_ITEMS__
</section>

<section>
  <h2><span class="bar"></span>二、PEP 標準自評（對照 J3 六大職能）</h2>
  <p class="section-note">每項列「對應指標 #N + 具體案例」。無案例者標「尚無案例」，方便判斷是否補。自評不強制標等級。</p>
  __COMPS__
</section>

<section>
  <h2><span class="bar"></span>三、核心價值（本人事蹟）</h2>
  <p class="section-note">五大核心價值；同組成員觀察請自行補上（本工具不含他人資料）。</p>
  __CORE_VALUES__
</section>

<footer>由 JIRA (JKO) 與 RD3 週報自動整理草稿 ・ 對照 J3 PEP 標準 ・ Eric Liao</footer>
</div>
</body>
</html>"""

# 用既有報告的 <style> 內容當基底（複製 assets/build_report_example.py 的 :root ~ footer 樣式）
BASE_STYLE = open(BASE + "/_base_style.css", encoding="utf-8").read()

out = (TEMPLATE
    .replace("__BASE_STYLE__", BASE_STYLE)
    .replace("__KPI__", kpi_html)
    .replace("__TTW__", ttw_html)
    .replace("__WORK_ITEMS__", wi_html)
    .replace("__COMPS__", comp_html)
    .replace("__CORE_VALUES__", cv_html))

# 全篇無內嵌 JSON，可整篇 linkify（把敘事中的 JKO-#### 轉連結）
out = linkify_jko(out)

open(BASE + "/Eric_2026H1_PEP自評.html", "w", encoding="utf-8").write(out)
print(f"PEP HTML written: {len(out)} chars | 指標覆蓋 {ind_covered}/{total_ind} | 核心價值事蹟 {n_cv_cases} | TTW 候選 {len(MAP.get('top_two_wins', []))}")
```

- [ ] **Step 2: 擷取既有報告的基底 CSS 成 `_base_style.css`**

Run（把 `build_report_example.py` 第 192–266 行的 CSS 內容——即 `:root{...}` 到 `@media...` 之間——抽出存檔；產生器讀它當基底樣式）：
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report"
python - <<'PY'
import re
src = open("assets/build_report_example.py", encoding="utf-8").read()
css = src[src.index(":root{"):src.index("</style>")]
open("reports/2026H1/_base_style.css","w",encoding="utf-8").write(css)
print("base style css chars:", len(css))
PY
```
Expected: 印出 css 長度（數千字元）。`reports/2026H1/_base_style.css` 建立。

- [ ] **Step 3: 用骨架 mapping 跑產生器**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python build_pep_report.py
```
Expected: `PEP HTML written: <數萬> chars | 指標覆蓋 0/29 | 核心價值事蹟 0 | TTW 候選 0`

- [ ] **Step 4: 驗證 HTML 結構（骨架階段）**

Run:
```bash
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
grep -c "details class=\"comp\"" Eric_2026H1_PEP自評.html   # 應為 6（六職能）
grep -c "尚無案例" Eric_2026H1_PEP自評.html                 # 應為 29（骨架每指標一個）
grep -q "</html>" Eric_2026H1_PEP自評.html && echo "html closed OK"
```
Expected: `6`、`29`、`html closed OK`。

- [ ] **Step 5: 檢查點 — 骨架產生器可運作**

確認 `Eric_2026H1_PEP自評.html` 可用瀏覽器開、六職能可折疊、樣式正常。此時內容為空骨架，內容於 Task 5 填入。

---

## Task 5: 自動起草 `pep_mapping.json`（並行 subagent 分析 152 項）

**Files:**
- Modify: `reports/2026H1/pep_mapping.json`（由空骨架填入草稿內容）
- Read: `data/jira_h1_2026.json`、`data/rd3_weekly_part1~4.md`、`Eric_2026H1_已完成工作總整理.html`（既有主軸敘事）

- [ ] **Step 1: 準備給 subagent 的精簡佐證清單**

Run（產一份「key → summary/type/labels/parentSummary」精簡表，供 subagent 對照，不必讀 400KB 原始檔）：
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python - <<'PY'
import json
BASE="."
data=json.load(open(BASE+"/data/jira_h1_2026.json",encoding="utf-8"))
comp=set(json.load(open(BASE+"/data/completed_h1_keys.json",encoding="utf-8")))
rows=[{"key":r["key"],"summary":r.get("summary"),"type":r.get("issuetype"),
       "labels":r.get("labels"),"epic":r.get("parentSummary")} for r in data if r.get("key") in comp]
json.dump(rows,open(BASE+"/data/_evidence_index.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("evidence index rows:",len(rows))
PY
```
Expected: `evidence index rows: 152`

- [ ] **Step 2: 並行分派 subagent 起草各職能映射**

用 6 個並行 subagent（每職能一個），各自讀 `data/_evidence_index.json`、`data/rd3_weekly_part1~4.md`、既有主軸敘事，依 `pep_catalog.py` 該職能的指標，起草 `evidence`（{key, case}）。**規則寫進每個 subagent 的 prompt：**
- 只寫 Eric 本人做的事；動詞精準（發現/驗證/協調/跟進，不攬功）。
- 每個 case 引用的 key 必須 ∈ 152 完成單，且 case 內容須與該 key 的正式 summary 相符。
- case 句式：`在 XX 專案完成 XX 工作，有 XX 的成果`。
- 寧缺勿濫：沒有紮實佐證的指標留空，不硬湊。
- 各 subagent 回傳該職能的 JSON 片段（精簡），不要把原始資料塞回主 context。

另用 1 個 subagent 起草 `work_items`（沿用既有六大主軸濃縮成條列）、`core_values`（本人事蹟）、`top_two_wins`（挑影響力最大者，可多列）。

- [ ] **Step 3: 合併片段寫回 `pep_mapping.json`**

把各 subagent 回傳的片段合併進 `pep_mapping.json`（填 `competencies.*.indicators`、`work_items`、`core_values`、`top_two_wins`）。用 Edit/Write 寫檔，UTF-8。

- [ ] **Step 4: 驗證 mapping 合法**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python validate_mapping.py
```
Expected: `PASS: mapping 結構正確；共 N 筆指標佐證、M 件 Top Two Wins 候選`（N、M > 0）。若 FAIL（例如 key 不在完成單），修正 mapping 後重跑至 PASS。

- [ ] **Step 5: 產出含實際內容的 HTML**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python build_pep_report.py
grep -c "尚無案例" Eric_2026H1_PEP自評.html   # 應明顯 < 29（多數指標已有案例）
```
Expected: 印出指標覆蓋（如 `指標覆蓋 22/29`）；「尚無案例」數量下降。

---

## Task 6: 逐職能與 Eric 對焦 curate

**Files:**
- Modify: `reports/2026H1/pep_mapping.json`（依 Eric 回饋調整）

- [ ] **Step 1: 逐職能呈現草稿給 Eric**

依序把六職能（＋工作項目、核心價值、Top Two Wins）的草稿映射摘要呈現給 Eric，請他增刪案例、修正措辭、決定保留哪些指標。一次一個職能，避免一次太多。

- [ ] **Step 2: 套用回饋、重新驗證與產出**

每輪回饋後修改 `pep_mapping.json`，並重跑：
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python validate_mapping.py && python build_pep_report.py
```
Expected: 每輪皆 `PASS` 且 HTML 重新產出。重複至 Eric 滿意。

- [ ] **Step 3: 檢查點 — 內容定稿**

Eric 確認六職能自評、工作項目、核心價值、Top Two Wins 候選皆正確、只寫本人工作、單名無誤。

---

## Task 7: 更新 `SKILL.md`

**Files:**
- Modify: `~/.claude/skills/work-summary-report/SKILL.md`

- [ ] **Step 1: 新增「PEP 自評報告模式」章節**

在 SKILL.md 適當位置新增章節，內容涵蓋：
- 用途：從既有工作總整理資料重新映射成公司 PEP 填寫素材（工作項目 / 六職能自評 / 核心價值 / Top Two Wins 候選）。
- 產物：`pep_catalog.py`（J3 指標目錄，來源 Confluence 1669660766）、`pep_mapping.json`（可 curate 佐證映射，只帶 evidence）、`validate_mapping.py`、`build_pep_report.py`。
- 工作流：重用 `data/` → 自動起草 mapping（並行 subagent、寧缺勿濫、對照正式單名、只寫本人）→ `validate_mapping.py` → `build_pep_report.py` → 逐職能與使用者 curate。
- 內容規則：Show don't tell（每指標要具體案例）、自評不強制標等級、核心價值只放本人事蹟。

- [ ] **Step 2: 更新「資料夾與檔案衛生」為新慣例**

把舊的「某處/期間-工作總整理」描述改為 `~/.claude/skills/work-summary-report/reports/<period>/`（per-period），並說明個人資料落在 skill 目錄的取捨（個人 skill、預設不 commit/同步；分享 skill 時 `reports/` 不隨附）。

- [ ] **Step 3: 檢查點 — SKILL.md 一致**

Run:
```bash
grep -n "PEP\|reports/\|pep_mapping\|build_pep_report" "/c/Users/eric.liao/.claude/skills/work-summary-report/SKILL.md"
```
Expected: 新章節與新資料夾慣例都在；無殘留舊的「Documents/期間-工作總整理」為唯一慣例的描述。

---

## Task 8: 交付與清理

**Files:**
- Cleanup: `reports/2026H1/data/_evidence_index.json`（暫存）
- 詢問: 是否刪除舊備份 `Documents/2026H1-工作總整理/`

- [ ] **Step 1: 最終自我核對**

Run:
```bash
export PYTHONIOENCODING=utf-8
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
python validate_mapping.py
python build_pep_report.py
grep -o 'href="https://jkopay.atlassian.net/browse/JKO-[0-9]*"' Eric_2026H1_PEP自評.html | wc -l   # JKO 連結數 > 0
```
Expected: `PASS`、HTML 重新產出、JKO 連結數 > 0。

- [ ] **Step 2: 清掉暫存中間檔**

Run:
```bash
cd "/c/Users/eric.liao/.claude/skills/work-summary-report/reports/2026H1"
rm -f data/_evidence_index.json
ls
```
Expected: 只剩正式檔（`pep_catalog.py`、`pep_mapping.json`、`validate_mapping.py`、`build_pep_report.py`、`build_report.py`、`_base_style.css`、兩個 HTML、`data/`）。

- [ ] **Step 3: 交付摘要給 Eric**

給出：PEP HTML 路徑、開啟指令 `start "" "C:\Users\eric.liao\.claude\skills\work-summary-report\reports\2026H1\Eric_2026H1_PEP自評.html"`、本次內容摘要（六職能覆蓋、Top Two Wins 候選件數）。

- [ ] **Step 4: 詢問是否刪除舊備份資料夾**

問 Eric：新位置已可正常重跑，是否刪除舊備份 `C:\Users\eric.liao\Documents\2026H1-工作總整理\`？**未得同意前不刪。**

---

## Self-Review

**1. Spec coverage：**
- 雙重交付（能力＋Eric 2026H1 報告）→ Task 1-4（能力）、Task 5-6（實際報告）。✓
- HTML 輸出、沿用風格 → Task 4（`_base_style.css` 重用、TEMPLATE）。✓
- 自動草稿＋curate → Task 5（並行 subagent 起草）、Task 6（curate）。✓
- 重用 2026H1 資料 → Task 0 遷移、各 Task 讀 `data/`。✓
- J3 指標 → Task 1 `pep_catalog.py`。✓
- 核心價值只本人 → Task 5 Step 2、Task 4 段落三。✓
- Top Two Wins 候選 → Task 4（面板）、Task 5（起草）。✓
- 資料夾 reports/<period>/ + 遷移 → Task 0、Task 7 Step 2。✓
- SKILL.md 更新 → Task 7。✓
- 遷移與清理（刪除前問）→ Task 0（複製不刪）、Task 8 Step 4。✓
- 內容規則（只本人/正式單名/linkify/不標等級）→ Task 5 Step 2 prompt、validator、Task 6。✓
- 範圍界線（不產 docx/不多職級/不接 API）→ 計畫未觸及，符合。✓

**2. Placeholder scan：** 無 TBD/TODO；code 步驟均含完整程式碼；CSS 以「複製 example 指定行」方式重用（Task 4 Step 2 用腳本自動擷取，非手動 placeholder）。✓

**3. Type consistency：** `pep_catalog.CATALOG`（comp_key→(name, {num:text})）、`CORE_VALUES`（list of (key,name)）在 generator/validator 一致；`pep_mapping.json` 的 `competencies.<key>.indicators.<num>.evidence[].{key,case}`、`core_values.<key>.cases[].{key?,case}`、`top_two_wins[].{title,impact,evidence[]}` 在 skeleton、validator、generator 三處一致；helper 名 `summary_of`/`linkify_jko`/`esc` 一致。✓
