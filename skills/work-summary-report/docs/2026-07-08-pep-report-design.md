# PEP 自評報告功能設計（work-summary-report skill 擴充）

- 日期：2026-07-08
- 狀態：設計已與 Eric 確認，待複核 → 轉入實作規劃
- 2026-07-08 實作後調整：PEP 報告**移除「工作項目」段**（改由既有「已完成工作總整理」報告擔任，避免重複維護）；輸出**拆為兩份 HTML**（`PEP標準自評`＝六職能＋Top Two Wins、`核心價值`），對應公司 docx 區塊。以 SKILL.md 現況為準。
- 作者：Eric + Claude
- 主題：為 `work-summary-report` skill 新增「PEP 期中績效自評報告」產出能力

---

## 1. 背景與目標

公司每半年進行一次「期中績效考評」，由三部分組成：

- **Top Two Wins**：上回饋平台填寫，聚焦「影響力」（最多 2 件事）。
- **PEP 填寫**：用公司指定的 Google Doc 格式填寫，聚焦「能力定位與成長方向」，對照 Career Ladder 職級行為指標。
- **Team Lead 面談**：1-on-1。

現有 `work-summary-report` skill 已能從 **JIRA 完成單 + RD3 週報** 萃取「工作總整理」HTML。本次要新增的功能，是**建立在同一批已蒐集資料上**，把成果「重新映射」成 **PEP 填寫**所需的段落，並輸出一份自包含 HTML，作為填寫公司 PEP 文件與 Top Two Wins 的素材來源。

### 本次實作的雙重交付

本次任務同時交付兩件事：

1. **可重複使用的能力**：新的產生器、映射檔慣例、SKILL.md 更新、`reports/<period>/` 資料夾結構——之後每半年可重跑。
2. **Eric 本人的 2026H1 PEP 報告**：以本期實際資料跑完整流程（自動草稿 → Eric curate → 產 HTML），產出可用的 `Eric_2026H1_PEP自評.html`。

### 目標讀者與用途

這份 PEP HTML 是 **Eric 本人填寫公司 PEP／Top Two Wins 的素材與草稿**，不是直接交付給主管的文件（總結欄由 Team Lead 在 1-on-1 填）。價值在於：把 152 項完成工作，自動對應到 PEP 六大職能的行為指標並附具體案例，省去手動盤點的力氣，再由 Eric 策略性篩選。

---

## 2. 需求來源文件

- 2026 後端期中績效考評指引（Confluence 2049933314）
- PEP 自評指南與 Career Ladder（Confluence 1668251685）
- PEP 與其他回饋機制的差異（Confluence 2033680391）
- **J3 資深軟體工程師 PEP 標準（Confluence 1669660766）← 自評對照基準**
- 各角色技術能力參考範例（Confluence 1699119254）
- `Backend PEP Template.docx`（填寫格式範本，位於 skill 根目錄）
- 現有 `SKILL.md`、`assets/build_report_example.py`

### PEP 範本（docx）段落結構

| 段落 | 誰填 | 內容 |
|---|---|---|
| 1. 工作項目 | 本人 | 條列本期主要工作/專案（業務專案、技術專案、其他：文件、分享），格式不拘、條列＋簡短描述。 |
| 2. PEP 標準自評 | 本人 | 對照六大職能，逐項列「符合的行為指標＋具體案例」。格式：`對應指標：技術能力 #1「快速定位問題根源」，在 XX 專案完成 XX 工作有 XX 的成果`。 |
| 3. 核心價值 | 本人 | 列自己或同組成員符合五大核心價值的具體事蹟。 |
| 4. 總結 | Team Lead | 1-on-1 時填 → **本功能不產出**。 |

---

## 3. 已鎖定決策

| # | 決策 | 選定 |
|---|---|---|
| 1 | 輸出格式 | 自包含 HTML（沿用現有報告視覺風格） |
| 2 | 映射方式 | Claude 自動起草完整映射（JSON），Eric 再策略性篩選/curate |
| 3 | 資料來源 | 重用既有 `2026H1` 已蒐集、已核對的資料，不重跑 JQL/週報 |
| 4 | 對照職級 | J3 資深軟體工程師 |
| 5 | 核心價值範圍 | 只產 Eric 本人事蹟（同組成員部分 Eric 手動補） |
| 6 | Top Two Wins | 順便產「候選素材」（可多列供挑選） |
| 7 | 檔案落點 | 收進 skill 底下 `reports/<period>/`，per-period；並把既有 `Documents/2026H1-工作總整理/` 遷移過去 |

**期間**：2026 H1。完成項目數：152（含 JKO 單與 INCIDENT）。

---

## 4. 架構（方案 A：獨立產生器＋獨立 HTML、共用 data/）

新增 `build_pep_report.py`，與現有 `build_report.py` 並存、共讀同一份 `data/`；新增一份可 curate 的映射檔 `pep_mapping.json`；輸出獨立的 `Eric_2026H1_PEP自評.html`。

理由：符合現有 skill「一支聚焦的可重跑產生器、印出關鍵數字自我核對」的精神；PEP 正式素材與工作總整理（自己/主管回顧用）分開，各自產生器好維護；現有工作總整理不受影響。

（已排除方案 B「併進同一多頁籤 HTML」——一支產生器變肥、兩種讀者混雜；方案 C「通用模板引擎」——過度設計。）

---

## 5. 資料夾結構（新慣例）

```
~/.claude/skills/work-summary-report/
├── SKILL.md                          ← 更新：新增 PEP 模式 + 新資料夾慣例
├── docs/
│   └── 2026-07-08-pep-report-design.md   ← 本設計文件
├── assets/
│   └── build_report_example.py
└── reports/
    └── 2026H1/                       ← 從 Documents/2026H1-工作總整理 遷移
        ├── data/                     ← 共用原始資料
        │   ├── jira_h1_2026.json
        │   ├── completed_h1_keys.json
        │   └── rd3_weekly_part1~4.md
        ├── build_report.py           ← 既有（BASE 改指到此）
        ├── build_pep_report.py       ← 新增：PEP 產生器
        ├── pep_mapping.json          ← 新增：可 curate 的映射檔（核心產物）
        ├── Eric_2026H1_已完成工作總整理.html   ← 既有（遷移）
        └── Eric_2026H1_PEP自評.html            ← 新增
```

**取捨備註**：個人績效資料會長住在 skill 目錄。因這是 `~/.claude/skills/` 下的個人 skill（非共享 plugin、預設不 commit/同步），私密性可接受。若日後分享此 skill，`reports/` 不隨附。

---

## 6. 核心產物：`pep_mapping.json`

「工作佐證 → PEP 指標」的映射檔，Claude 自動起草、Eric curate。產生器讀它 + `data/` 產 HTML；Eric 改 JSON 重跑即可（同現有工作流）。

```jsonc
{
  "level": "J3",
  "period": "2026H1",

  // → 段落一「工作項目」：沿用現有主軸分組，濃縮成條列
  "work_items": [
    { "theme": "保險平台遷移", "category": "業務專案",
      "desc": "API 層翻寫與串接於 2025 完成，本期灰度上線、切換與舊系統退役",
      "keys": ["JKO-...", "JKO-..."] }
  ],

  // → 段落二「PEP 標準自評」：六大職能，指標編號對齊 J3 標準頁
  "competencies": {
    "technical":     { "name": "技術能力 Technical Excellence",
      "indicators": {
        "1": { "text": "快速定位問題根源／線上問題快速恢復並提出事件總結",
               "evidence": [ { "key": "JKO-27897", "case": "調閱國壽 UAT 保單異常 Log，快速定位…有…成果" } ] }
      } },
    "leadership":    { "name": "領導力與影響力 Leadership & Influence", "indicators": { } },
    "delivery":      { "name": "交付與當責 Delivery & Accountability", "indicators": { } },
    "communication": { "name": "溝通與協作 Communication & Collaboration", "indicators": { } },
    "business":      { "name": "業務與策略 Business & Strategy", "indicators": { } },
    "ai":            { "name": "AI 素養與應用 AI Literacy & Application", "indicators": { } }
  },

  // → 段落三「核心價值」：只放 Eric 本人事蹟
  "core_values": {
    "user_first":        { "name": "先從用戶出發", "cases": [ { "key": "...", "case": "..." } ] },
    "candor":            { "name": "大膽坦率", "cases": [] },
    "break_inertia":     { "name": "跳脫慣性", "cases": [] },
    "fast_and_accurate": { "name": "非常快儘量準", "cases": [] },
    "all_in":            { "name": "全心投入", "cases": [] }
  },

  // → Top Two Wins 候選（可 >2 件供挑選；口徑是「影響力」不是完成度）
  "top_two_wins": [
    { "title": "...", "impact": "...", "evidence": ["JKO-..."] }
  ]
}
```

### 指標目錄（產生器內建的 J3 canonical catalog，來源：Confluence 1669660766）

產生器內建下列指標清單（即使某指標無佐證也照列，讓 Eric 一眼看出哪些沒案例）：

- **技術能力** #1 快速定位/線上恢復+事件總結；#2 前瞻性分析方案、提前識別風險並提架構調整；#3 中大型專案技術統整與決策、掌握全局；#4 核心任務中任務梳理與協調實作同仁；#5 跨多技術領域（Coding/CI-CD/基礎設施）；#6 準確同步資訊給利害關係人、遇阻迅速反映；#7 Code Review 提供建設性意見協助成員。
- **領導力與影響力** #1 指導初階工程師；#2 協助成員設定成長方向與練習機會；#3 依團隊能力規劃執行計畫；#4 多角度建設性回饋；#5 討論中協助收斂可執行方向。
- **交付與當責** #1 可行計畫、按時達標、品質高標；#2 獨立評估研究歸納方案；#3 主動即時提出專案風險；#4 主動承擔責任、看到問題就動手；#5 上線後有足夠監控與告警。
- **溝通與協作** #1 跨團隊協調相依工作與交付時間；#2 主動提高可行意見、分解與分配任務；#3 會議中整理關鍵重點；#4 主持會議有明確摘要與進程。
- **業務與策略** #1 持續分享專業知識、建立信任感；#2 對業務範圍提建設性建議；#3 熟悉並推廣公司政策方向；#4 落實管理工具並協助同事。
- **AI 素養與應用** #1 策略性應用；#2 品質治理（Code Review 把關 AI 產出）；#3 團隊賦能（分享 AI 技巧）；#4 流程改善（AI 整合開發流程）。
- **核心價值**（不評分）：先從用戶出發、大膽坦率、跳脫慣性、非常快儘量準、全心投入。

---

## 7. 產生器 `build_pep_report.py`

- `BASE` 絕對路徑指向 `reports/2026H1/`，可原地重跑。
- 讀 `data/jira_h1_2026.json`（取 JKO 正式 summary、做 linkify）＋ `pep_mapping.json`。
- 輸出自包含、離線可開、UTF-8 的 `Eric_2026H1_PEP自評.html`。
- 沿用 `assets/build_report_example.py` 的 CSS / JKO linkify / 折疊區塊為藍本改，不從零寫。
- 最後印出關鍵數字（六職能各涵蓋幾個指標/幾張佐證單、核心價值事蹟數、Top Two Wins 候選數）供自我核對。

### HTML 段落（沿用現有視覺風格）

1. **KPI 卡**：本期完成 152 項、六職能涵蓋 N 個指標、5 核心價值、Top Two Wins 候選數。
2. **Top Two Wins 候選**：獨立醒目面板，標明「另填在回饋平台、談影響力」。
3. **一、工作項目**：沿用既有主軸分組，濃縮成條列＋簡短描述（業務／技術／其他）。
4. **二、PEP 標準自評**：六職能可折疊；每職能下列「對應指標 #N「指標名」→ 佐證單＋草稿案例句」；每職能掛「涵蓋 N 單」徽章。
5. **三、核心價值**：五大價值各列 Eric 本人具體事蹟。

所有 JKO 皆為可點連結（`https://jkopay.atlassian.net/browse/JKO-####`，開新分頁）；linkify 不得破壞內嵌 JSON。

---

## 8. 自動草稿流程（152 項 + 週報 → `pep_mapping.json` 草稿）

- 依現有 skill 鐵則走「**存檔 → Python 處理 → 只回精簡結果**」，不把大原始資料讀進主 context。
- 152 項分類分析量大，**開並行 subagent** 分批讀 `data/`（JIRA json＋週報＋現有主軸敘事），各自起草 `pep_mapping.json` 片段（分職能或分主軸），再合併成完整草稿。
- 草稿是起點，非定稿：
  - 每個指標的案例句都**對照 JKO 正式 summary**（沿用既有報告已核對過的正確單名）。
  - **只寫 Eric 本人做的事**、動詞精準（發現/驗證/協調/跟進，不攬功）。
  - 產完**逐職能請 Eric 篩選**（增刪案例、調整措辭、決定哪些指標要保留）。

---

## 9. Top Two Wins 候選

- 從 152 項挑「影響力最大」的候選（例：保險平台遷移灰度上線、重大事故 RCA、自建上線驗證 skill…）。
- 每件寫「做了什麼 ＋ 帶來什麼改變」，**口徑是影響力（不是完成度）**。
- **可多列幾件**供 Eric 到回饋平台時挑 1–2 件。寫進 `pep_mapping.json` 的 `top_two_wins`，並在 HTML 獨立面板呈現。

---

## 10. 內容規則

**沿用既有 skill 鐵則**：只寫本人工作；動詞精準；對照 JIRA 正式單名；內部服務名不過度解釋；排除週報雜訊（完成度%／週次／單項工時）；JKO linkify 且不破壞內嵌 JSON。

**PEP 專屬**：
- Show don't tell — 每個保留的指標都要有**具體案例**。
- 自評**不強制**標等級（成長中/穩定展現/超越期望），預設不標；Eric 要標再加。
- 核心價值只放 Eric 本人事蹟（同組成員 Eric 手動補）。

---

## 11. SKILL.md 更新

- 新增「PEP 自評報告模式」章節：段落結構、`pep_mapping.json` 映射檔、`build_pep_report.py` 產生器、J3 指標對照來源（Confluence 連結）、自動草稿＋curate 工作流。
- 「資料夾與檔案衛生」章節改為新的 `reports/<period>/` 慣例（取代舊的「某處/期間-工作總整理」描述），並說明個人資料落在 skill 目錄的取捨。

---

## 12. 遷移與清理

1. 建立 `reports/2026H1/`，把 `Documents/2026H1-工作總整理/` 內容（`data/`、`build_report.py`、既有 HTML）搬進去。
2. 更新 `build_report.py` 的 `BASE` 指向新位置，重跑確認工作總整理 HTML 仍正常產出。
3. **舊資料夾 `Documents/2026H1-工作總整理/`：在新位置確認可正常重跑後、刪除前再問 Eric 一次**，不自作主張刪。

---

## 13. 範圍界線（YAGNI）

**不做**：Word .docx 輸出、多職級切換（本次只 J3）、接回饋平台 API、自動抓同事資料、自動送出/上傳任何內容。

---

## 14. 交付與自我核對

- 每次改 `pep_mapping.json` 後重跑產生器，並用 Python/grep 驗證：字串已換、無殘留 placeholder、JSON 仍可解析、JKO 連結數正確、內嵌 JSON 未被 linkify 破壞。
- 完成後給 Eric：報告路徑、開啟指令（`start "" "<path>"`）、本輪內容摘要。
- 逐職能與 Eric 對焦草稿；有疑慮就問，不猜。
