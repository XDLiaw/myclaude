# -*- coding: utf-8 -*-
import json, html, collections, re

BASE = r"C:/Users/eric.liao/Documents/2026H1-工作總整理"
alldata = json.load(open(BASE+"/data/jira_h1_2026.json", encoding="utf-8"))

# ---- 口徑：只納入「完成時間落在 2026 上半年」的單（不論開單時間）----
# completed_h1_keys.json 來自 JQL：assignee was currentUser() DURING H1
#   AND status CHANGED TO ("完成","Done") DURING ("2026/01/01","2026/06/30")
# 已與「resolutiondate 落在 H1」的集合雙重核對一致（152 張，零差異）。
COMPLETED_KEYS = set(json.load(open(BASE+"/data/completed_h1_keys.json", encoding="utf-8")))
data = [r for r in alldata if r.get("key") in COMPLETED_KEYS]

def area_of(labels):
    L = set(labels or [])
    if "叫車" in L: return "叫車"
    if "繳費" in L: return "繳費"
    if "保險" in L: return "保險"
    for x in L:
        if x.startswith("捐款"): return "捐款"
    return "其他/未分類"

AREA_COLOR = {"保險":"#2563eb","繳費":"#16a34a","捐款":"#db2777","叫車":"#ea580c","其他/未分類":"#64748b"}
def ac(a): return AREA_COLOR.get(a, "#64748b")
def esc(s): return html.escape(s or "")

# 把文字中的 JKO-#### 轉為可點擊連結（僅用於可見的敘事區塊，不套用於嵌入的 JSON）
JKO_BASE = "https://jkopay.atlassian.net/browse/"
def linkify_jko(text):
    return re.sub(r'JKO-\d+',
                  lambda m: f'<a class="jko" href="{JKO_BASE}{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>',
                  text)

# ---------- aggregates on completed set ----------
TOTAL = len(data)
by_area = collections.Counter(area_of(r.get("labels")) for r in data)
by_type = collections.Counter(r.get("issuetype") for r in data)
by_epic = collections.Counter((r.get("parentSummary") or "（無 Epic）") for r in data)
created_2026 = sum(1 for r in data if (r.get("created") or "")[:4] == "2026")
created_before = sum(1 for r in data if (r.get("created") or "")[:4] < "2026" and r.get("created"))
# 每月完成數（以結案日 resolutiondate 認定，已核對與 changelog 一致）
cm = collections.Counter((r.get("resolutiondate") or "")[:7] for r in data)

# 各主軸涵蓋的完成單數（依領域；繳費再依關鍵字分「信件系統」vs「醫療費/票交」）
def is_medical(r):
    s = (r.get("summary") or "") + " " + (r.get("parentSummary") or "")
    return any(k in s for k in ("醫療費", "轉票交", "票交", "醫療"))
ebpp = [r for r in data if area_of(r.get("labels")) == "繳費"]
cover = {
    "A": by_area.get("保險", 0),
    "B": sum(1 for r in ebpp if not is_medical(r)),
    "C": sum(1 for r in ebpp if is_medical(r)),
    "D": by_area.get("捐款", 0),
    "E": by_area.get("叫車", 0),
}

# ---------- KPI ----------
kpi = [
    (str(TOTAL), "本期完成單數", "完成時間落在 2026 上半年（不論開單時間）"),
    (str(by_area.get("保險",0)), "保險", "上半年完成最大宗（平台遷移＋維運）"),
    (str(by_area.get("繳費",0)), "繳費", "信件系統 + 醫療費/票交"),
    (str(by_area.get("捐款",0)), "捐款", "維運、類別標籤等"),
    (str(by_area.get("叫車",0)), "叫車", "維運與事件處理"),
    (str(by_area.get("其他/未分類",0)), "其他", "跨模組/未標記領域"),
]
kpi_html = "".join(
    f'<div class="kpi"><div class="kpi-num">{n}</div><div class="kpi-label">{l}</div><div class="kpi-sub">{s}</div></div>'
    for n,l,s in kpi
)

# ---------- Area table ----------
areas_order = ["保險","繳費","捐款","叫車","其他/未分類"]
area_rows = ""
for a in areas_order:
    tot = by_area.get(a,0)
    pct = tot/TOTAL*100 if TOTAL else 0
    area_rows += (
        f'<tr><td><span class="dot" style="background:{ac(a)}"></span>{a}</td>'
        f'<td class="num">{tot}</td>'
        f'<td class="num">{pct:.1f}%</td></tr>'
    )
area_rows += (
    f'<tr class="total-row"><td>合計</td><td class="num">{TOTAL}</td>'
    f'<td class="num">100%</td></tr>'
)

# ---------- Type bars ----------
type_map = [("Task","Task 任務","#4f46e5"),("Bug","Bug 缺陷","#dc2626"),
            ("Sub-task","Sub-task 子任務","#0891b2"),("Story","Story 需求","#16a34a"),
            ("Epic","Epic","#9333ea")]
type_html = ""
for k,lab,col in type_map:
    v = by_type.get(k,0)
    if v == 0: continue
    pct = v/TOTAL*100 if TOTAL else 0
    type_html += (
        f'<div class="srow"><div class="slab" style="width:120px">{lab}</div>'
        f'<div class="strack"><div class="sfill" style="width:{pct:.1f}%;background:{col}"></div></div>'
        f'<div class="sval">{v}</div></div>'
    )

# ---------- Month bar chart (created & completed, 2026 H1) ----------
months = ["2026-01","2026-02","2026-03","2026-04","2026-05","2026-06"]
mlabel = {"2026-01":"1月","2026-02":"2月","2026-03":"3月","2026-04":"4月","2026-05":"5月","2026-06":"6月"}
mx = max(cm.get(m,0) for m in months) or 1
month_bars = ""
for m in months:
    v = cm.get(m,0); h = int(v/mx*140)+2
    month_bars += (
        f'<div class="mbar-col"><div class="mbar-val">{v}</div>'
        f'<div class="mbar" style="height:{h}px"></div>'
        f'<div class="mbar-lab">{mlabel[m]}</div></div>'
    )

# ---------- Top epics (completed only) ----------
def epic_area_guess(name):
    if "保險" in name: return "保險"
    if "捐款" in name or "捐" in name: return "捐款"
    if "繳費" in name or "醫療費" in name or "信件" in name or "檔案傳送" in name: return "繳費"
    if "叫車" in name: return "叫車"
    return "其他/未分類"
epic_html = ""
for name,cnt in by_epic.most_common(22):
    a = epic_area_guess(name)
    epic_html += (
        f'<tr><td><span class="dot" style="background:{ac(a)}"></span>{esc(name)}</td>'
        f'<td class="num">{cnt}</td></tr>'
    )

# ---------- Timeline (from weekly reports) ----------
timeline = [
 ("W1","12/29–01/02","保險","保險 argo job 上線；富邦 JWT 5 支 API 完成支援；舊保險翻 Java 第 3 階段 30%→35%。因保險公司未開通新 IP 白名單，流量暫導回舊保險。"),
 ("W2","01/05–01/09","保險","舊保險灰度遷移上 PROD，建單/查單/退款三支 API 開放 10%→20%；額外開發測試 API 驗證 PROXY 連通性。"),
 ("W3","01/12–01/16","保險","灰度提升至 50%、onlinepay callback 開 10%；PROXY(210.17.19.129) 除國泰外皆成功銷案；富邦 JWT UAT 五支 API 通過。"),
 ("W4","01/19–01/23","保險","翻 Java 50%→60% 測試完成；修復 3 個保險 BUG（qr_timeout 精度致明台解析錯誤、國泰付款方式欄位、4 筆認列）。"),
 ("W5","01/26–01/30","保險","保險加 LOG/告警、遮罩敏感資料、修 URL 編碼；新增「取得會員資訊 API」取代 WEB 直呼 UAPI 的資安風險；捐款 DB 緩慢排查。"),
 ("W6","02/02–02/06","保險","翻 Java 60%→80%；新增 LOG 與十多個 Alert 上 UAT。"),
 ("W7","02/09–02/13","保險","翻 Java 80%→100%；叫車維運追查用戶回饋，判定為 App 11.13.0 上下車地點顯示 bug。"),
 ("W8","02/16–02/20","其他/未分類","（農曆年假期，無週報）"),
 ("W9","02/23–02/26","保險","保險上版監控 + 灰度逐步放量；翻 Java 第 3 階段 100%。組內分享自建「保險上線驗證」Claude Skill（補告警做不到的正向驗證，284 筆銷案零錯誤、7 間保險公司全覆蓋）與 Claude DevTools。"),
 ("W10","03/02–03/06","保險","灰度開至 100%；發現富邦/國泰系統寫死舊 IP 繞過 API Gateway；WEB 改呼叫保險平台防外洩。分享 Claude Code 權限設定 + PreToolUse Hook。維運 onlinepay 建單失敗（保險 3 筆 / 捐款 34 筆）。"),
 ("W11","03/09–03/13","保險","灰度維持 100%；國泰完成 IP 切換、富邦延至 3/30。"),
 ("W12","03/16–03/20","保險","舊保險排程翻寫上版；撥款日排程改新 domain 解決 K8s 連通；修正退款 SQL 因 fee_setting_id 多為 NULL 被濾掉。"),
 ("W13","03/23–03/27","繳費","啟動技術專案「串接 RD4 信件寄送系統」(初步 design)；保險排程調校（DailyTransactionReportJob 誤設 dryRun）；API 流量全導向新保險。維運國泰 API KEY 過期、叫車圖資錯誤。"),
 ("W14","03/30–04/02","保險","保險富邦端 WAF 未設定致網投銷案被攔、暫還原；即查繳 API 正常。RD4 信件系統續作。"),
 ("W15","04/07–04/10","繳費","RD4 信件寄送系統 0%→20%（04/07 design review、04/17 核心功能 + POC 兩封信上 SIT）。"),
 ("W16","04/13–04/17","繳費","RD4 20%→30%；保險 2.5d 帳差維運：網投 Callback 被 EXPIRED 阻擋 + status=null NPE，共 9 筆訂單，重產交易報表並重跑撥款排程。"),
 ("W17","04/20–04/24","繳費","RD4 30%→40%；保險維運工具 Design Review；捐款 onlinepay 擋單維運。"),
 ("W18","04/27–04/30","保險","保險「停產報表機制」0%→100%（04/30 SIT、05/06 PROD）；RD4 QA 測試。"),
 ("W19","05/04–05/08","繳費","RD4 40%→50%；富邦 JWT 切換驗證完成（新舊驗簽並存）；INCIDENT-34 後續優化 0%→100%。"),
 ("W20","05/11–05/15","叫車","RD4 50%→60%；發現保險 JOB 異步 event 致 main thread 提早結束問題；叫車 1d 惡意用戶事件排查（比對大車隊清單、DB 撈 jkoId、標籤系統隱藏入口）。"),
 ("W21","05/18–05/22","繳費","RD4 60%→90%；凱擘 B-5/B-7 改為 per-vendor recipientGroupId、20 vendor 各自寄送、移除舊 email backstage API。"),
 ("W22","05/25–05/29","繳費","RD4 信件寄送系統 90%→100%，05/27 PROD 全面切換完成、上版監控。"),
 ("W23","06/01–06/05","捐款","捐款「類別標籤顯示/隱藏」規劃（PRD/Design review 排程）；保險 06/02 更版。"),
 ("W24","06/08–06/12","捐款","台北市醫療費 Survey 起步；捐款類別標籤 0%→100% 上 SIT；保險更版。"),
 ("W25","06/15–06/18","繳費","醫療費進 Design（06/25 Design Review）；保險客訴 RCA（JKO-31317 明台網投，判定非保險系統問題）。"),
 ("W26","06/22–06/26","繳費","轉票交-醫療費 0%→10%；撈取泰安產險 2026 年交易險種明細（維運）。"),
 ("W27","06/29–07/03","繳費","轉票交-醫療費 10%→40%（建單 API / callback / 退款服務）；叫車 taxi_trip_tab 新增索引。"),
]
tl_html = ""
for w,d,a,txt in timeline:
    tl_html += (
        f'<div class="tl-item"><div class="tl-dot" style="background:{ac(a)}"></div>'
        f'<div class="tl-body"><div class="tl-head"><span class="tl-week">{w}</span>'
        f'<span class="tl-date">{d}</span>'
        f'<span class="tag" style="background:{ac(a)}18;color:{ac(a)};border-color:{ac(a)}55">{a}</span></div>'
        f'<div class="tl-text">{esc(txt)}</div></div></div>'
    )

# ---------- issues list for table (completed only) ----------
mini = []
for r in data:
    mini.append({
      "key":r.get("key"),"summary":r.get("summary"),"type":r.get("issuetype"),
      "area":area_of(r.get("labels")),"epic":r.get("parentSummary") or "",
      "res":(r.get("resolutiondate") or "")[:10],"created":(r.get("created") or "")[:10],
      "prio":r.get("priority"),"url":r.get("webUrl"),
      "labels":[x for x in (r.get("labels") or []) if x not in ("module_paymentApp","rd3_sprint")],
      "old": bool(r.get("created")) and (r.get("created") or "")[:4] < "2026",
    })
mini.sort(key=lambda r:(r["res"] or "0000", r["created"] or "0000"), reverse=True)
ISSUES_JSON = json.dumps(mini, ensure_ascii=False)
AREA_COLOR_JSON = json.dumps(AREA_COLOR, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eric Liao — 2026 上半年已完成工作總整理</title>
<style>
:root{--bg:#f6f7fb;--card:#fff;--ink:#1e293b;--muted:#64748b;--line:#e5e8f0;--accent:#4f46e5;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;line-height:1.65;}
.wrap{max-width:1180px;margin:0 auto;padding:32px 22px 80px;}
header.hero{background:linear-gradient(135deg,#4f46e5,#7c3aed 55%,#db2777);color:#fff;border-radius:20px;padding:38px 40px;box-shadow:0 12px 30px rgba(79,70,229,.25);}
header.hero h1{margin:0 0 6px;font-size:30px;letter-spacing:.5px;}
header.hero .sub{opacity:.92;font-size:15px;}
header.hero .meta{margin-top:16px;font-size:13px;opacity:.85;display:flex;gap:20px;flex-wrap:wrap;}
header.hero .meta b{font-weight:600;}
section{margin-top:38px;}
h2{font-size:21px;margin:0 0 4px;display:flex;align-items:center;gap:10px;}
h2 .bar{width:5px;height:22px;background:var(--accent);border-radius:3px;display:inline-block;}
.section-note{color:var(--muted);font-size:13.5px;margin:0 0 18px;}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-top:22px;}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px;box-shadow:0 2px 8px rgba(30,41,59,.04);}
.kpi-num{font-size:30px;font-weight:700;color:var(--accent);line-height:1;}
.kpi-label{font-size:13.5px;font-weight:600;margin-top:6px;}
.kpi-sub{font-size:11.5px;color:var(--muted);margin-top:4px;line-height:1.4;}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 24px;box-shadow:0 2px 8px rgba(30,41,59,.04);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.grid-3-2{display:grid;grid-template-columns:1.3fr 1fr;gap:18px;}
table{width:100%;border-collapse:collapse;font-size:13.5px;}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;}
th{color:var(--muted);font-weight:600;font-size:12.5px;background:#fafbff;}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;}
.total-row td{font-weight:700;border-top:2px solid var(--line);background:#fafbff;}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;vertical-align:middle;}
.mchart{display:flex;align-items:flex-end;gap:18px;height:190px;padding:10px 4px 0;}
.mbar-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;}
.mbar{width:70%;max-width:52px;background:linear-gradient(180deg,#6366f1,#4f46e5);border-radius:6px 6px 0 0;}
.mbar-val{font-size:13px;font-weight:700;color:var(--accent);margin-bottom:5px;}
.mbar-lab{font-size:12px;color:var(--muted);margin-top:7px;}
.srow{display:flex;align-items:center;gap:10px;margin:9px 0;}
.slab{width:58px;font-size:13px;color:var(--muted);}
.strack{flex:1;background:#eef0f6;border-radius:6px;height:14px;overflow:hidden;}
.sfill{height:100%;border-radius:6px;}
.sval{width:60px;text-align:right;font-size:12.5px;font-variant-numeric:tabular-nums;}
.theme{background:var(--card);border:1px solid var(--line);border-left-width:4px;border-radius:0 12px 12px 0;padding:18px 22px;margin:14px 0;box-shadow:0 2px 8px rgba(30,41,59,.04);}
.theme h3{margin:0 0 8px;font-size:16.5px;}
.theme .thtag{font-size:11.5px;font-weight:600;padding:2px 9px;border-radius:20px;margin-left:8px;vertical-align:middle;border:1px solid;}
.theme ul{margin:8px 0 0;padding-left:20px;}
.theme li{margin:5px 0;font-size:14px;}
.theme .tickets{margin-top:10px;font-size:12px;color:var(--muted);}
.theme .subhead{margin:14px 0 2px;font-size:13.5px;font-weight:700;color:#334155;border-top:1px dashed var(--line);padding-top:10px;}
.theme .cover{font-size:11px;font-weight:600;color:var(--muted);margin-left:8px;background:#f1f5f9;border:1px solid var(--line);border-radius:20px;padding:2px 9px;vertical-align:middle;white-space:nowrap;}
.chip{display:inline-block;background:#eef2ff;color:#4338ca;border-radius:6px;padding:1px 7px;margin:2px 3px 0 0;font-size:11.5px;font-family:ui-monospace,Menlo,Consolas,monospace;}
a.jko{color:#4338ca;text-decoration:none;font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:600;}
a.jko:hover{text-decoration:underline;}
.chip a.jko{color:inherit;font-weight:400;}
.theme ul ul{margin:6px 0 4px;padding-left:20px;}
.theme ul ul li{font-size:13px;margin:3px 0;color:#334155;}
.tl{position:relative;margin-top:8px;padding-left:8px;}
.tl-item{position:relative;padding:0 0 4px 30px;margin-bottom:14px;border-left:2px solid var(--line);}
.tl-item:last-child{border-left:2px solid transparent;}
.tl-dot{position:absolute;left:-8px;top:3px;width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 1px var(--line);}
.tl-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.tl-week{font-weight:700;font-size:14px;}
.tl-date{font-size:12.5px;color:var(--muted);}
.tag{font-size:11px;font-weight:600;padding:1px 9px;border-radius:20px;border:1px solid;}
.tl-text{font-size:13.5px;margin-top:3px;}
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 14px;}
.filters input[type=text]{padding:7px 11px;border:1px solid var(--line);border-radius:8px;font-size:13px;min-width:220px;}
.fbtn{padding:6px 13px;border:1px solid var(--line);background:#fff;border-radius:20px;font-size:12.5px;cursor:pointer;color:var(--muted);}
.fbtn.active{background:var(--accent);color:#fff;border-color:var(--accent);}
.tbl-wrap{max-height:640px;overflow:auto;border:1px solid var(--line);border-radius:12px;}
#tbl{font-size:12.8px;}
#tbl th{position:sticky;top:0;z-index:2;}
#tbl td a{color:#4338ca;text-decoration:none;font-family:ui-monospace,Consolas,monospace;font-weight:600;}
#tbl td a:hover{text-decoration:underline;}
.newtag{font-size:10px;color:#16a34a;border:1px solid #bbf7d0;background:#f0fdf4;border-radius:5px;padding:0 5px;margin-left:6px;}
.oldtag{font-size:10px;color:#9333ea;border:1px solid #e9d5ff;background:#faf5ff;border-radius:5px;padding:0 5px;margin-left:6px;}
.count-note{font-size:12.5px;color:var(--muted);margin-left:auto;}
.callout{background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:14px 18px;font-size:13.5px;color:#7c2d12;}
footer{margin-top:50px;text-align:center;color:var(--muted);font-size:12px;}
@media(max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.grid2,.grid-3-2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">

<header class="hero">
  <h1>2026 上半年 已完成工作總整理</h1>
  <div class="sub">Eric Liao ・ 技術部 RD3 ・ 資料來源：JIRA (JKO) + RD3 團隊週報 ・ <b>僅列已完成單</b></div>
  <div class="meta">
    <span><b>期間</b> 2026-01-01 ~ 2026-06-30</span>
    <span><b>本期完成 JIRA</b> 152 張（完成時間落在 H1）</span>
    <span><b>週報</b> W1–W27（W8 農曆年無）</span>
    <span><b>產出日</b> 2026-07-07</span>
  </div>
</header>

<section><div class="kpis">__KPI__</div></section>

<section>
  <div class="callout">
   <b>口徑說明：</b>本報告以「<b>完成時間落在 2026 上半年（2026-01-01 ~ 06-30）</b>」為準，<b>共 152 張已完成單，不論開單時間</b>——以「狀態轉為完成」的變更時間認定，並經 resolutiondate 雙重核對一致（零差異）。已排除仍進行中、待處理、及 ICE BOX 擱置的單。
   152 張中 <b>141 張為 2026 年開立、11 張為 2024/2025 舊單於本期結案</b>；領域分佈：保險 94 / 繳費 23 / 捐款 17 / 叫車 6 / 其他 12。（先前「掛名完成 588」的口徑會把 2025 已結案的長尾舊單一併計入而虛胖，本版已改正。）
  </div>
</section>

<section>
  <h2><span class="bar"></span>一、上半年重點工作主軸</h2>
  <p class="section-note">依週報整理出的六大主軸，橫跨保險平台上雲與維運、繳費平台新專案、捐款與叫車維運，以及 AI 導入。所列皆為已完成或已上線之工作（維運/事故已歸入所屬專案）。各主軸標題的「涵蓋 N 張」＝該領域本期完成單數，其下「代表單」為其中精選；五大領域合計 <b>140</b> 張，另有其他/未標記 12 張未另立主軸，總計 152 張（詳見第四區完整清單）。</p>

  <div class="theme" style="border-left-color:#2563eb">
    <h3>A. 保險平台 — 翻寫 Java 上雲、灰度遷移與維運事故（Q1–Q2 主線）<span class="thtag" style="color:#2563eb;border-color:#2563eb;background:#2563eb14">保險</span><span class="cover">涵蓋 __CNT_A__ 張完成單</span></h3>
    <div class="subhead">遷移與翻寫（舊系統翻 Java 上雲）</div>
    <ul>
      <li><b>舊保險翻寫 Java 第 3 階段</b>：延續前兩階段（API 層：建單／查單／退款／onlinepay callback 已翻寫並灰度上線），第 3 階段聚焦把舊保險的<b>批次排程與報表產製</b>翻寫為 Java 並改用 Argo Workflow job 上 K8s。實際項目：
        <ul>
          <li>翻寫「交易日報表」排程並補齊測試（DailyTransactionReport）— JKO-23992</li>
          <li>翻寫「手續費月報表」：主體開發 → 測試撰寫與重構（Test &amp; refactor）→ 產檔改串接 MinIO 儲存（原系統未串接，含各環境權限與 bucket 申請）→ Argo Workflow job GitOps 設定與上線 — JKO-26052、JKO-26235、JKO-26460、JKO-26927、JKO-26594</li>
          <li>撥款日排程（FillDisburseDateJob）優化 — JKO-25302</li>
          <li>年後上版內容盤點與排程 — JKO-26236</li>
          <li>上線後排程調校與修正：撥款日排程（FillDisburseDateJob）改新 domain 解 K8s 連通、修正 DailyTransactionReportJob 誤設 dryRun、修正退款 SQL fee_setting_id NULL 濾除問題</li>
        </ul>
      </li>
      <li><b>灰度遷移上線</b>（API Gateway 串接已於 2025 完成，H1 進行正式上線切換）：建單／查單／退款／onlinepay callback API 透過 PROXY 逐步放量 10%→100%、全程監控銷案成功率；上線期間另以<b>自建 Claude Skill</b> 自動分析 LOG 做正向驗證（詳見主軸 F）。最終移除 API Gateway feature flag、固定導向新保險服務（JKO-28117）。</li>
      <li><b>富邦 JWT 串接與切換完成</b>：完成 5 支 API 的 JWT 串接，PROD 上線並切換為新舊驗簽並存。</li>
      <li><b>API Gateway / IP 白名單治理</b>：發現國泰、富邦系統寫死舊 IP（繞過 Gateway 直打 legacy VM），並在兩家調整後驗證流量已正確導回 Gateway。</li>
      <li><b>🏁 遷移完成 &amp; 舊 VM 回收（里程碑）</b>：確認灰度 100% 後舊保險 VM 已無殘留流量（JKO-26967）、舊保險排程停用並切換至新排程（JKO-28323），最終關閉並回收舊 Python 保險 VM、釋放資源（JKO-29804）——<b>新舊保險完全切換、legacy 系統正式退役</b>。</li>
    </ul>
    <div class="subhead">平台強化</div>
    <ul>
      <li><b>資安強化</b>：遮罩 API LOG 敏感資料（JKO-25569）；新增「取得會員資訊 API」取代 WEB 直呼 UAPI 的資安風險（單號待確認）。</li>
      <li><b>可觀測性</b>：補充 LOG 與監控告警、新增十多個 Alert（JKO-25707）、修正 API URL 的 LOG 編碼問題（JKO-25568）；callback API 低流量告警調整（3 支 monitoring/service-check MR，JKO-26377）。</li>
    </ul>
    <div class="subhead">維運、事故與 RCA</div>
    <ul>
      <li><b>網路投保（網投）Callback 帳差事件</b>：過期訂單重複呼叫被 <code>EXPIRED</code> 阻擋（6 筆）、status=null 致 callback NPE（3 筆），共 9 筆訂單帳務對不上。處理：
        <ul>
          <li>將被 PaymentStatusSyncJob 誤壓為 <code>EXPIRED</code> 的訂單還原為 <code>ACCEPT</code>（DB 異動）— JKO-28729</li>
          <li>修復泰安產險未銷案的交易（DB 異動）— JKO-28699</li>
          <li>重產並上傳每日交易報表(T檔)、重跑撥款日排程</li>
        </ul>
      </li>
      <li><b>INCIDENT-34 後續優化</b>：開發「付款狀態手動同步 API」並調整 PaymentStatusSyncJob——原 JOB 主邏輯以非同步 Event 執行，main thread 會提早結束而中止未完成的 handler；改版修正，並提供手動同步 API 作備援 — JKO-29107</li>
      <li><b>onlinepay 不可用事故（3/5，保險端）</b>：onlinepay 中斷致 3 筆保險訂單建單失敗，系統當下正確回傳建單失敗、未造成錯帳；彙整此次異常對保險的影響範圍 — JKO-27004</li>
      <li><b>客訴與維運調查</b>：明台網投客訴調查（確認非保險系統問題，JKO-31317）、撈取泰安產險 2026 年交易險種明細（JKO-31597）、協助調閱國壽 UAT 建立保單異常之 Log（JKO-27897）</li>
      <li><b>保險 BUG 修復</b>：明台產險無法交易（建單 API 回傳的 qr_timeout 精度與舊系統不同，致明台解析錯誤、用戶無法付款，JKO-25558）、國泰人壽帳務 PAYMENT_TOOL 為 NULL（銷帳 API 帶的 Request 欄位與舊系統有差異，致付款方式未正確儲存，JKO-25575）、灰度切換期間 4 筆銷案失敗訂單處理（經國泰確認已認列，JKO-25436）</li>
    </ul>
    <div class="tickets">代表單：<span class="chip">JKO-23992</span><span class="chip">JKO-26052</span><span class="chip">JKO-24774</span><span class="chip">JKO-24999</span><span class="chip">JKO-25458</span><span class="chip">JKO-27038</span><span class="chip">JKO-25707</span><span class="chip">JKO-28699</span><span class="chip">JKO-29107</span><span class="chip">JKO-31317</span></div>
  </div>

  <div class="theme" style="border-left-color:#16a34a">
    <h3>B. 繳費平台 — 串接 RD4 信件寄送系統（Q2 主線，已完成上線）<span class="thtag" style="color:#16a34a;border-color:#16a34a;background:#16a34a14">繳費</span><span class="cover">涵蓋 __CNT_B__ 張完成單</span></h3>
    <ul>
      <li><b>技術專案負責人</b>（design 啟動至 05/27 PROD 全面切換上線），歷時約 2.5 個月。</li>
      <li><b>POC 先行</b>：宜蘭停車銷案逾時、公有停車場扣款失敗、票交通用告警、凱擘統整報表等範本上線。</li>
      <li><b>全面切換至 RD4 Mail Delivery（MD）系統</b>：將剩餘全部信件改由 RD4 的 MD（Mail Delivery）系統寄送。</li>
      <li><b>凱擘 per-vendor 改版</b>：B-5/B-7 日報/月報改 per-vendor recipientGroupId、20 家 vendor 各自寄送、移除舊 email backstage API。</li>
    </ul>
    <div class="tickets">代表單：<span class="chip">JKO-27049</span><span class="chip">JKO-28317</span><span class="chip">JKO-28318</span><span class="chip">JKO-28319</span><span class="chip">JKO-28468</span><span class="chip">JKO-28498</span><span class="chip">JKO-29108</span><span class="chip">JKO-29485</span><span class="chip">JKO-29512</span><span class="chip">JKO-28314</span></div>
  </div>

  <div class="theme" style="border-left-color:#16a34a">
    <h3>C. 繳費平台 — 台北市醫療費 / 轉票交（Q2 後段，已完成前期階段）<span class="thtag" style="color:#16a34a;border-color:#16a34a;background:#16a34a14">繳費</span><span class="cover">涵蓋 __CNT_C__ 張完成單</span></h3>
    <ul>
      <li><b>已完成 Survey 與 Design</b>：完成需求 Survey 與 Design Review，並展開開發（延續至下半年）。</li>
      <li>已產出建單 API（多筆子單）、Onlinepay Callback、共用退款服務（MtchRefundService）等設計與初步實作。</li>
    </ul>
    <div class="tickets">代表單：<span class="chip">JKO-30840</span><span class="chip">JKO-31131</span><span class="chip">JKO-31370</span><span class="chip">JKO-31525</span><span class="chip">JKO-31578</span></div>
  </div>

  <div class="theme" style="border-left-color:#db2777">
    <h3>D. 捐款模組維運與優化<span class="thtag" style="color:#db2777;border-color:#db2777;background:#db277714">捐款</span><span class="cover">涵蓋 __CNT_D__ 張完成單</span></h3>
    <div class="subhead">開發與優化</div>
    <ul>
      <li><b>類別標籤顯示/隱藏</b>：完成開發並上 SIT。</li>
      <li><b>授扣 domain 更換</b>：換新 domain 並 SIT 測試成功。</li>
    </ul>
    <div class="subhead">維運與事故</div>
    <ul>
      <li><b>捐款 DB 緩慢問題排查（尚未解決）</b>：已排除 AP 層（非應用端問題）；至今仍未找出根因，DB 持續緩慢、暫無解，持續追蹤。</li>
      <li><b>onlinepay 不可用事故（3/5，捐款端）</b>：同一事故致 34 筆捐款訂單建單失敗（系統同樣正確回傳錯誤、未錯帳）；事後改善 onlinepay 錯誤識別與 log level，並補強 authpay／merchant-module 外部服務錯誤識別 — JKO-27040</li>
      <li>多項捐款版本維運（2.0 / 2.1 / v3.5.0 等）。</li>
    </ul>
    <div class="tickets">代表單：<span class="chip">JKO-25690</span><span class="chip">JKO-18820</span><span class="chip">JKO-18821</span><span class="chip">JKO-30843</span><span class="chip">JKO-30761</span><span class="chip">JKO-27040</span></div>
  </div>

  <div class="theme" style="border-left-color:#ea580c">
    <h3>E. 叫車維運與事件處理<span class="thtag" style="color:#ea580c;border-color:#ea580c;background:#ea580c14">叫車</span><span class="cover">涵蓋 __CNT_E__ 張完成單</span></h3>
    <ul>
      <li><b>惡意用戶事件排查</b>：依大車隊清單從 DB 撈 jkoId、分析歷史紀錄判斷真偽，提供 PM 用標籤系統隱藏叫車入口。</li>
      <li>用戶回饋追查（判定為 App 11.13.0 顯示 bug）、大車隊圖資錯誤地址。</li>
      <li><b>DB 效能</b>：taxi_trip_tab 新增 idx_job_id 索引（~3.2M rows，避免 full table scan）。</li>
    </ul>
    <div class="tickets">代表單：<span class="chip">JKO-29940</span><span class="chip">JKO-29949</span><span class="chip">JKO-27893</span><span class="chip">JKO-30588</span><span class="chip">JKO-31626</span></div>
  </div>

  <div class="theme" style="border-left-color:#0891b2">
    <h3>F. AI / Claude Code 導入與組內分享<span class="thtag" style="color:#0891b2;border-color:#0891b2;background:#0891b214">效率</span></h3>
    <ul>
      <li><b>自建「保險上線驗證」Claude Skill（自建工具、無 JIRA 票；組內分享）</b>：為灰度上線打造的 LOG 自動分析工具，<b>補足傳統告警做不到的「正向驗證」</b>——告警只能偵測「錯誤發生」，無法確認「每間保險公司都成功走完整個新流程、格式與機敏資料正確」。功能涵蓋：
        <ul>
          <li>流量監控、各保險公司切換至新翻寫 API 的比例</li>
          <li>錯誤統整與分析</li>
          <li>驗證新程式流程是否完整觸發、走過</li>
        </ul>
        並串接 Git diff → Release Note → 上版計畫 → LOG 檢查清單 → 持續驗證報告（自動發布 Confluence）。本次保險上版（59 commits、74 檔案）產 55 項 LOG 檢查清單、跑 13 次驗證循環，<b>成果：284 筆銷案零錯誤、7 間保險公司全覆蓋</b>。</li>
      <li><b>Claude Code 權限設定 + PreToolUse Hook</b>：無害操作放行、危險操作才攔截。</li>
      <li><b>Claude DevTools 分享</b>：token 用量、Debug、subagent 工作流優化。</li>
    </ul>
  </div>
</section>

<section>
  <h2><span class="bar"></span>二、數據分析（本期完成 152 張）</h2>
  <p class="section-note">左：各領域本期完成量與占比；右：完成單的類型分佈。</p>
  <div class="grid2">
    <div class="card">
      <h3 style="margin:0 0 10px;font-size:15px;">業務領域分佈（本期完成）</h3>
      <table>
        <thead><tr><th>領域</th><th class="num">完成數</th><th class="num">占比</th></tr></thead>
        <tbody>__AREA_ROWS__</tbody>
      </table>
      <p style="font-size:11.5px;color:var(--muted);margin:10px 0 0;"><b>保險（94）為本期完成最大宗</b>；捐款回落至 17（2025 已完成的長尾舊單不計入本口徑）。合計 152 張。</p>
    </div>
    <div class="card">
      <h3 style="margin:0 0 10px;font-size:15px;">完成單類型分佈</h3>
      __TYPE__
      <p style="font-size:11.5px;color:var(--muted);margin:14px 0 0;">以 Task 為主（149 張），另含 2 張 Bug、1 張 Story。</p>
    </div>
  </div>

  <div class="grid-3-2" style="margin-top:18px;">
    <div class="card">
      <h3 style="margin:0 0 6px;font-size:15px;">每月完成數（2026 H1）</h3>
      <div class="mchart">__MONTH_BARS__</div>
    </div>
    <div class="card">
      <h3 style="margin:0 0 10px;font-size:15px;">主要 Epic（完成單數 Top）</h3>
      <div style="max-height:230px;overflow:auto;">
      <table><thead><tr><th>Epic</th><th class="num">完成數</th></tr></thead><tbody>__EPIC_ROWS__</tbody></table>
      </div>
    </div>
  </div>
</section>

<section>
  <h2><span class="bar"></span>三、逐週時間軸（RD3 週報）</h2>
  <p class="section-note">W1–W27 每週回報重點（保險 / 繳費 / 捐款 / 叫車 / 維運）。</p>
  <div class="tl">__TIMELINE__</div>
</section>

<section>
  <h2><span class="bar"></span>四、本期完成 JIRA 清單（152 張，可篩選）</h2>
  <div class="filters">
    <input type="text" id="q" placeholder="搜尋單號 / 摘要 / Epic…" oninput="render()">
    <button class="fbtn active" data-f="all" onclick="setF(this)">全部</button>
    <button class="fbtn" data-f="保險" onclick="setF(this)">保險</button>
    <button class="fbtn" data-f="繳費" onclick="setF(this)">繳費</button>
    <button class="fbtn" data-f="捐款" onclick="setF(this)">捐款</button>
    <button class="fbtn" data-f="叫車" onclick="setF(this)">叫車</button>
    <button class="fbtn" data-f="其他/未分類" onclick="setF(this)">其他</button>
    <span class="count-note" id="cnt"></span>
  </div>
  <div class="tbl-wrap">
    <table id="tbl">
      <thead><tr><th>單號</th><th>摘要</th><th>領域</th><th>類型</th><th>Epic</th><th>建立</th><th>結案</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</section>

<footer>由 JIRA (JKO) 與 RD3 團隊週報自動整理 ・ 僅列本期完成單（完成時間落在 2026 H1）・ 產出於 2026-07-07 ・ Eric Liao</footer>
</div>

<script>
const ISSUES = __ISSUES__;
const AREA_COLOR = __AREA_COLOR__;
let curF = "all";
function setF(btn){
  curF = btn.getAttribute("data-f");
  document.querySelectorAll(".fbtn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  render();
}
function render(){
  const q = document.getElementById("q").value.trim().toLowerCase();
  const tb = document.getElementById("tbody");
  let rows = ISSUES.filter(r=>{
    if(curF!=="all" && r.area!==curF) return false;
    if(q){
      const hay = (r.key+" "+r.summary+" "+(r.epic||"")+" "+(r.labels||[]).join(" ")).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
  let buf=[];
  for(const r of rows){
    const col = AREA_COLOR[r.area] || "#64748b";
    buf.push('<tr>'+
      '<td><a href="'+r.url+'" target="_blank" rel="noopener">'+r.key+'</a></td>'+
      '<td>'+linkJko(escapeHtml(r.summary))+(r.old?'<span class="oldtag">跨年結案</span>':'')+'</td>'+
      '<td><span class="dot" style="background:'+col+'"></span>'+r.area+'</td>'+
      '<td>'+r.type+'</td>'+
      '<td style="color:#64748b;font-size:11.5px;">'+linkJko(escapeHtml(r.epic||"—"))+'</td>'+
      '<td style="white-space:nowrap;color:#64748b;">'+(r.created||"")+'</td>'+
      '<td style="white-space:nowrap;color:#64748b;">'+(r.res||"—")+'</td>'+
      '</tr>');
  }
  tb.innerHTML = buf.join("");
  document.getElementById("cnt").textContent = "顯示 "+rows.length+" / "+ISSUES.length+" 張";
}
function escapeHtml(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function linkJko(s){return (s||"").replace(/JKO-\d+/g, m=>'<a class="jko" href="https://jkopay.atlassian.net/browse/'+m+'" target="_blank" rel="noopener">'+m+'</a>');}
render();
</script>
</body>
</html>"""

out = (TEMPLATE
  .replace("__KPI__", kpi_html)
  .replace("__AREA_ROWS__", area_rows)
  .replace("__TYPE__", type_html)
  .replace("__MONTH_BARS__", month_bars)
  .replace("__EPIC_ROWS__", epic_html)
  .replace("__TIMELINE__", tl_html)
  .replace("__CNT_A__", str(cover["A"]))
  .replace("__CNT_B__", str(cover["B"]))
  .replace("__CNT_C__", str(cover["C"]))
  .replace("__CNT_D__", str(cover["D"]))
  .replace("__CNT_E__", str(cover["E"]))
  .replace("__ISSUES__", ISSUES_JSON)
  .replace("__AREA_COLOR__", AREA_COLOR_JSON))

# 只 linkify <script> 之前的可見 HTML（敘事、時間軸、chips），避免動到嵌入的 JSON 而破壞 JS
_i = out.find("<script>")
out = linkify_jko(out[:_i]) + out[_i:]

open(BASE+"/Eric_2026H1_已完成工作總整理.html","w",encoding="utf-8").write(out)
print("completed-in-H1:", TOTAL, "| created-2026:", created_2026, "| created-before:", created_before, "| cover:", cover, "| by_area:", dict(by_area))
print("HTML written:", len(out), "chars")
