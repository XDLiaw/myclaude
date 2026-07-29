---
name: jira-ticket-creator
description: 協助在 JIRA 上建立票券（Issue）。當使用者要開 JIRA 單／開票／建票、建立 Task/Story/Bug、或開一張票追蹤某問題／需求時使用（含一般票、上版票、DB 異動單、維運票）。自動查詢專案慣例（Labels、Parent Epic、Sprint），整理欄位與使用者確認後才建立。支援 JKO 及其他 Atlassian 專案。
allowed-tools:
  - Read
  - Glob
  - Grep
  - mcp__claude_ai_Atlassian__createJiraIssue
  - mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
  - mcp__claude_ai_Atlassian__getJiraIssue
  - mcp__claude_ai_Atlassian__editJiraIssue
  - mcp__claude_ai_Atlassian__lookupJiraAccountId
  - mcp__claude_ai_Atlassian__getVisibleJiraProjects
  - mcp__claude_ai_Atlassian__getJiraProjectIssueTypesMetadata
  - mcp__claude_ai_Atlassian__addCommentToJiraIssue
---

# JIRA Ticket Creator Skill

協助使用者在 JIRA 上建立票券，自動查詢專案慣例並確認所有欄位後才建立。

## 核心原則

**絕對不要在未經使用者明確確認前建立票券。** 所有欄位必須先整理出來讓使用者確認，使用者說「開單」或類似明確指令後才執行建立。

## JIRA 環境

| 項目 | 值 |
|------|------|
| Site | `jkopay.atlassian.net` |
| Cloud ID | `jkopay.atlassian.net`（用於 API 呼叫的 cloudId 參數） |
| 使用者 Account ID | `611e2372c6021e006954b849` |

## 使用者負責領域

> **本節是「目前」的參考快照，不是寫死的規則。** 使用者負責的領域會隨時間變動，本 skill 也可能分享給其他人使用——所以下面的領域／label 清單只是當前參考值，實際請依自己的責任範圍調整。真正要遵守的是「**每張票挑一個領域 label（互斥）＋ 視需要疊加技術 label**」這個機制，不是這幾個特定值。（同理，`## JIRA 環境` 的 Account ID、下方預設 labels `module_paymentApp`／`rd3_sprint`、`[RD3]` 前綴等，也都是此使用者／團隊的當前慣例，換人用時一併調整。）

使用者隸屬「支付應用模組」，目前負責以下專案領域：

### 領域 Labels（互斥，每張票選一個）

| 領域 | 額外 Label | 說明 |
|------|-----------|------|
| 保險 | `保險` | 保險投保、理賠、繳費相關 |
| 叫車 | `叫車` | 叫車服務、乘車碼相關 |
| 捐款 | `捐款` | 捐款功能相關 |

### 技術 Labels（可疊加）

| Label | 使用時機 |
|-------|---------|
| `argo_workflow` | 票券涉及 Argo Workflow / batch job / 排程任務時額外加上，可與領域 Label 並存 |
| `release` | 票券為上版票時加上（搭配標題 `[上版]` 與 release note 連結，詳見「上版票特殊處理」） |

**範例**：保險的 argo job 相關票券 → Labels: `module_paymentApp`, `rd3_sprint`, `保險`, `argo_workflow`

根據票券內容自動判斷所屬領域和是否需要技術 Label。如無法判斷，由使用者指定。

## 開票所需欄位

| # | 欄位 | API 參數 | 必填 | 說明 |
|---|------|----------|------|------|
| 1 | 專案 | `projectKey` | 是 | 如 `JKO` |
| 2 | 標題 | `summary` | 是 | 依專案慣例命名 |
| 3 | 類型 | `issueTypeName` | 是 | `Task` / `Story` / `Bug` |
| 4 | Sprint | `additional_fields.customfield_10020` | 否 | Sprint ID（放 Backlog 則不填） |
| 5 | Labels | `additional_fields.labels` | 否 | 字串陣列 |
| 6 | Parent | `parent` | 否 | 父 Issue Key（通常是 Epic） |
| 7 | Story Points | `additional_fields.customfield_10039` | 否 | 數值（**注意：是 `customfield_10039`（classic "Story Points"），不是 `customfield_10016`（"Story point estimate"）**） |
| 8 | 描述 | `description` | 否 | Markdown 格式 |
| 9 | 指派 | `assignee_account_id` | 否 | 預設指派給使用者自己 |
| 10 | Priority | `additional_fields.priority` | 否 | 如 `{"name": "P2"}` |

## 標題撰寫原則

- **標題只寫「問題／對象」本身，不寫解法或處置**：標題 = 對象＋環境＋問題現象（例：`國泰人壽 UAT 建立訂單 API 憑證信任失敗`）。處置做法（交付新 CA、重啟服務、調整設定…）屬描述的「目標」段，**不進標題**——混進去會讓標題冗長又失焦。
- 一般格式 `[RD3][<領域>] <問題現象>`；各票型另有前綴：上版加 `[上版]`、DB 異動加 `[DB異動]`、維運則把領域與維運**合併**為 `[RD3][<領域>維運]`（詳見各票型段落）。

## 描述內容撰寫指引

**核心原則：票的 description 只描述「目標與動機」——想做什麼、為什麼做、預期達成什麼。絕對不要把「具體做了什麼」（實作細節、逐項變更、commit 清單、檔名／類別／方法、測試內容）寫進 description。**

description 建議結構（兩段即可）：

1. **背景／動機** — 問題現象、影響範圍、觸發原因；可附佐證數據或報告／討論串連結。回答「為什麼要做」。
2. **目標** — 要達成什麼、預期效果。回答「要做到什麼」。

**「具體做了什麼」放哪裡：**
- 完整實作細節屬於**對應 MR 的 description**（逐項 commit、類別／方法、測試）。
- 若需要在**票上**補充實作摘要或貼 MR／commit 連結，一律**用 COMMENT 補充，不要寫進 description**——description 永遠只保留目標與動機。

> **例外：DB 異動單**——SQL／DDL 本身就是交付物（專案無 Flyway，需手動對 PROD 執行），因此 SQL 要直接寫進 description，不適用上面「實作細節不進 description」的規則。詳見「DB 異動單（DB Migration Ticket）特殊處理」。

描述使用 Markdown 格式撰寫。

## 操作流程

### 步驟 1：確認專案

確認使用者要在哪個專案（projectKey）下建票。如果使用者未明確指定，根據對話上下文判斷（例如在保險專案的 workspace 中，預設為 `JKO`）。

### 步驟 2：查詢專案慣例

使用 JQL 查詢使用者在該專案下最近的票券，以了解：

1. **標題命名慣例** — 如 `[RD3][保險] xxx`
2. **常用 Labels** — 如 `module_paymentApp`, `rd3_sprint`, `保險`
3. **常用 Parent (Epic)** — 動態搜尋可用選項
4. **當前 Sprint** — 查詢 openSprints()

執行以下查詢（並行）：

```
# 查最近的票，取得 labels、parent、summary 慣例
JQL: project = {projectKey} AND assignee = 611e2372c6021e006954b849 ORDER BY created DESC
fields: summary, labels, parent, customfield_10039, status

# 查當前 Sprint
JQL: project = {projectKey} AND assignee = 611e2372c6021e006954b849 AND sprint in openSprints() ORDER BY created DESC
fields: summary, customfield_10020

# 查支付應用模組下可用的 Epic（作為 Parent 候選）
JQL: project = {projectKey} AND issuetype = Epic AND status != Done AND labels = module_paymentApp ORDER BY created DESC
fields: summary, status, labels
```

**重點**：
- **預設 Labels**：每張票預設帶上 `module_paymentApp` 和 `rd3_sprint`（此使用者／團隊的固定預設，換人用時調整）
- **額外 Labels**：根據票券內容自動判斷所屬領域，對應「使用者負責領域」表格中的 Label（如 `保險`、`叫車`、`捐款`、`argo_workflow`）。若無法判斷則詢問使用者
- **Parent**：**必須主動搜尋可用的 Epic 選項**，搜尋 `labels = module_paymentApp` 且未完成的 Epic，以選項清單形式呈現讓使用者選擇。不可寫死，也不可只從歷史票券推測

### Parent 選擇流程

搜尋到可用 Epic 後，整理為選項清單呈現給使用者，格式如下：

```markdown
### 可用的 Parent Epic

| # | Issue Key | 標題 | 狀態 |
|---|-----------|------|------|
| 1 | JKO-xxxxx | Epic 標題 | 開發 & 處理中 |
| 2 | JKO-xxxxx | Epic 標題 | 待處理 |
| ... | ... | ... | ... |

請選擇要掛在哪個 Epic 下（輸入編號），或不指定 Parent。
```

根據票券內容的領域，可以主動建議最可能的選項（例如保險相關的票建議掛在「保險開發 & 優化項目」下），但最終由使用者決定。

### 步驟 3：評估 Story Points

**若為上版票，跳過此步驟**（不評估、不填 Story Points 欄位）。

**若為維運票，跳過此步驟**（不評估、不填 Story Points 欄位，一律留白）。維運票的實際耗時由使用者依實際投入事後自行填入，不需事前預估。確認表格中 Story Points 欄位標示為「留白（依實際耗費填入）」。

**若為 DB 異動單，Story Points 固定 0.5**（不套用下方換算、不逐張評估）。詳見「DB 異動單（DB Migration Ticket）特殊處理」。

> **維運票判定**：使用者明確說「維運單／維運票」，或票券本質為用戶客訴／線上問題調查，或標題帶「維運」。
>
> **維運票標題／Label**：領域與維運**合併成一個 bracket**——`[RD3][<領域>維運] ...`（例 `[RD3][保險維運] ...`、`[RD3][捐款維運] ...`），**不是**分開的 `[<領域>][維運]`；labels 於預設 `module_paymentApp, rd3_sprint, <領域>` 之外**再加 `維運`**。

在整理欄位前，根據任務內容主動評估 Story Points。

**換算基準**：
- 1 Story Point = 1 個工作天（實際工作 5~6 小時）
- 0.5 = 半天內可完成（簡單設定、小修改）
- 1 = 一天可完成（單一功能開發、簡單調查）
- 2 = 兩天（中等功能開發、需要跨模組）
- 3 = 三天（較複雜功能、需要設計和測試）
- 5 = 一週（大功能、多模組影響）
- 8+ = 超過一週（應考慮拆票）

**評估考量**：
1. **開發時間** — 撰寫程式碼所需時間
2. **調查/研究時間** — 分析 LOG、查找原因、閱讀文件
3. **測試時間** — 單元測試、整合測試、手動驗證
4. **部署/驗證時間** — SIT/UAT 部署和驗證
5. **Code Review** — 等待和修改 review 意見

評估結果連同理由一併呈現在確認表格中，讓使用者決定是否調整。

### 步驟 4：整理欄位並確認

根據使用者需求和查詢結果，整理出所有欄位，以表格形式呈現給使用者確認：

```markdown
### 開票內容

| 欄位 | 值 |
|------|------|
| **專案** | JKO |
| **標題** | [RD3][保險] xxxxxx |
| **類型** | Task |
| **Sprint** | 不指定（放 Backlog） |
| **Labels** | `module_paymentApp`, `rd3_sprint`, `保險` |
| **Parent** | JKO-26138（26Q1C2 保險開發 & 優化項目） |
| **Story Points** | 2（見下方評估） |
| **指派** | 使用者自己 |
| **Priority** | P2 |

### Story Points 評估

**建議：2 點**（約 2 個工作天）

| 工作項目 | 預估時間 |
|---------|---------|
| 分析 LOG 找出 ~30s 模式的根因 | 3~4 hr |
| 檢查外部 API timeout / DB 慢查詢 / connection pool | 3~4 hr |
| 修復或調整設定 | 2~3 hr |
| 測試驗證 | 1~2 hr |

### 描述（草稿）— 只寫背景／動機 + 目標，不含實作細節

> ## 背景／動機
> （問題現象、影響、為什麼要做，可附報告／連結）
>
> ## 目標
> （要達成什麼、預期效果）

有需要調整的地方嗎？確認後跟我說開單我就建立。
```

### 步驟 5：等待確認後建立

使用者明確說「開單」、「建立」、「OK」等確認指令後，才呼叫 `mcp__claude_ai_Atlassian__createJiraIssue` 建立票券。

建立成功後，回報 Issue Key。

## 上版票（Deployment Ticket）特殊處理

上版票的詳細內容已寫在 Release Note（通常是 Confluence 頁面），因此 JIRA 票券**只放 release note 連結**，避免資訊在不同地方重複維護。

### 觸發條件（任一即啟用「上版票模式」）

- 使用者明確說「上版單」「上版票」「deployment ticket」「release ticket」
- 標題包含 `[上版]` / `[Release]` / `[Deploy]`
- 對話中已提供 release note 連結（例如 Confluence URL）

若僅靠單一弱訊號（例如只看到 URL 但未說明用途），請先向使用者確認再切換模式。

### 上版票 vs. 一般票 欄位差異

| 欄位 | 一般票 | 上版票 |
|------|--------|--------|
| **標題** | `[RD3][<領域>] xxx` | `[RD3][<領域>][上版] xxx`（自動補 `[上版]`） |
| **Labels** | 預設 + 領域 Label | 預設 + 領域 Label + **`release`** |
| **描述** | 只寫「背景／動機 + 目標」，**不含實作細節**（詳見「描述內容撰寫指引」） | **只放 release note 連結**，無其他內容 |
| **Story Points** | 主動評估並建議 | **完全跳過**（不評估、不填欄位） |
| **Parent / Sprint / Assignee / Priority / Type** | — | 與一般票相同 |

### 上版票描述格式

只放一行 Markdown 連結，例如：

```markdown
Release Note: https://jkopay.atlassian.net/wiki/spaces/.../pages/...
```

**取得 release note 連結的方式**：
1. 若同一對話中已使用 `release-note-generator` skill 產生 Confluence 頁面，直接沿用該 URL
2. 否則向使用者索取連結
3. **不要**自行編造或補充其他描述內容

### 上版票確認表格範例

```markdown
### 開票內容（上版票）

| 欄位 | 值 |
|------|------|
| **專案** | JKO |
| **標題** | [RD3][保險][上版] 26Q2C1 |
| **類型** | Task |
| **Sprint** | 26Q2C1 / Backlog |
| **Labels** | `module_paymentApp`, `rd3_sprint`, `保險`, `release` |
| **Parent** | JKO-xxxxx（…） |
| **指派** | 使用者自己 |
| **Priority** | P2 |

### 描述
Release Note: https://jkopay.atlassian.net/wiki/...

確認後跟我說開單我就建立。
```

## DB 異動單（DB Migration Ticket）特殊處理

DB 異動單的交付物就是「要在資料庫執行的 SQL」——專案沒有 Flyway，SQL 必須由 DBA 或開發者手動對 PROD 執行。正因為 SQL 本身就是這張票的內容，DB 異動單是「描述只寫目標與動機、實作細節不進 description」這條通用規則的**例外**：SQL 一定要寫進 description。

### 觸發條件（任一即啟用「DB 異動單模式」）

- 使用者明確說「開 DB 異動單」「DB migration 單」
- 標題含 `[DB異動]` / `DB異動` / `DB migration`
- 任務本質是資料庫異動——**涵蓋兩類，不只 schema**：
  - **Schema 變動（DDL）**：`ALTER TABLE`、`CREATE INDEX`、新增／修改欄位
  - **資料變動（DML）**：`UPDATE` / `DELETE` 修資料、backfill 回填、資料導正

### 標題

`[RD3][<領域>][DB異動] <變更摘要>`

- `[DB異動]` 放在領域 bracket 之後，當作第三個 bracket tag
- 末尾可選擇性標註支援的功能單 `(JKO-xxxxx)`——有就帶、沒有就略

範例：
- `[RD3][保險][DB異動] order_tab 新增 jkos_account 欄位 (JKO-31315)`
- `[RD3][保險][DB異動] order_tab 清除 status=7 (EXPIRED) 記錄`（純資料變動）

### 欄位（與一般票的差異）

| 欄位 | DB 異動單 |
|------|-----------|
| **類型** | Task |
| **Labels** | 預設 + 領域 Label（**無**額外 DB label） |
| **Story Points** | **固定 0.5**（不逐張評估、不套用步驟 3 的換算） |
| **描述** | 見下方「描述結構」——**SQL 一定要放進 description** |
| **Parent / Sprint / Assignee / Priority** | 與一般票相同 |

### 確定 DB 名稱（描述必附）

SQL 最終要由 DBA／開發者手動連上某台 MySQL、對某個 database（schema）執行。若票上沒寫清楚是「哪個 DB」，執行者只能回頭問或自己猜——這正是最該由這張票講明白的資訊。所以 description 一定要有一段標明 **PROD DB 名稱**。

> **這段只列 DB 名稱本身**（如 `insurance_pay_db`），不要把來源、`application-prod` 路徑、JDBC URL 或推導過程寫進票——那些屬於暫時性的佐證，留在對話中讓使用者核對即可，別佔票面。

決定 DB 名稱依序走這三步，**找到就停**：

1. **先查專案 CLAUDE.md 有沒有記過**
   讀專案的 CLAUDE.md（checked-in 的專案指令檔，含被 `@import` 進來的檔案；**不是** `CLAUDE.local.md`、也不是全域 `~/.claude/CLAUDE.md`），找是否已記錄 PROD DB 名稱（關鍵字如「PROD DB」「資料庫名稱」「DB 名稱」）。有就直接用，跳過下面兩步——這就是「記一次、之後不再重找／重問」的用意。

2. **從 `application-prod` 設定檔解析**
   用 Glob 找專案內 `application-prod.{yml,yaml,properties}`，讀 datasource 的 JDBC URL，從 `jdbc:mysql://<host>:<port>/<db_name>?...` 取出 `?` 前的 `<db_name>`（properties 檔對應 key 通常是 `spring.datasource.url`）。
   - URL 若用 placeholder（`${db_name}`、`${...}`）取不到字面值 → 當作「找不到」，走第 3 步。
   - 有**多個 datasource**（多 DB）→ 全部列出，請使用者指認這次異動打哪個 DB。
   - 若 `application-prod` 只覆寫 host、DB 名寫在 base `application.yml` → 一併看 base 檔。

3. **找不到就問使用者**
   明確告訴他「在 `application-prod` 找不到字面 DB 名稱（或有多個無法判斷）」，請他提供 PROD DB 名稱。

**取得後：自動回寫專案 CLAUDE.md**（除非第 1 步已從那讀到）
只要 DB 名稱是這次「新確定」的（第 2 步解析到、或第 3 步使用者提供），就把它寫進專案 CLAUDE.md，讓下次同專案的 DB 異動單直接命中第 1 步。DB schema 名稱只是識別碼、**非機敏**（連線 host／帳密才是機敏，那些不寫），放進 checked-in 的 CLAUDE.md 沒問題。建議格式——在專案 CLAUDE.md 找合適位置補，或新增一個小節：

```markdown
## 資料庫（DB）

| 環境 | DB 名稱 |
|------|---------|
| PROD | <db_name> |
```

專案若已有相關小節就近補一列即可，不用硬開新段落。回寫後跟使用者講一聲「已把 PROD DB 名稱記到 `<path>`，下次同專案不用再問」。

### 描述結構

用 Markdown，依序包含（標「選擇性」者視情況）：

1. **背景／異動說明** — 為什麼要動、支援哪張功能單（附 JKO-xxxxx）
2. **資料庫（DB 名稱）** — **只列 PROD DB 名稱本身**（如 `insurance_pay_db`），不附來源／推導過程／連線資訊。名稱如何決定見上方「確定 DB 名稱」
3. **SQL / DDL** — 實際語句放 `sql` 程式碼區塊；多步驟就編號（例：1. 新增欄位 → 2. 建索引 → 3. 回填）。純資料變動（改資料／backfill）也要把 SQL 完整寫出
4. **執行順序** — **預設：DDL／SQL 先執行、程式更版後續才上**（沒 Flyway，順序錯會炸）。明確寫「須在程式部署前執行」；若這次剛好相反才特別註明
5. **環境範圍** — 標明是否**僅 PROD**（常見：SIT/UAT 由開發自行處理，只有 PROD 需要這張單）
6. **表大小 & 預估耗時**（選擇性）— 動大表／建索引時附 row 數 + DDL 預估時間 + `ALGORITHM=INPLACE, LOCK=NONE`（或評估改走 pt-online-schema-change）
7. **退版 SQL / 風險與緩解 / 驗收條件**（選擇性）— 較複雜或高風險的異動才寫
8. **關聯** — 功能票、上版票、Parent Epic、設計文件、上版計畫連結

### DB 異動單確認表格範例

```markdown
### 開票內容（DB 異動單）

| 欄位 | 值 |
|------|------|
| **專案** | JKO |
| **標題** | [RD3][保險][DB異動] order_tab 新增 xxx 欄位 (JKO-xxxxx) |
| **類型** | Task |
| **Sprint** | 26Q2C1 / Backlog |
| **Labels** | `module_paymentApp`, `rd3_sprint`, `保險` |
| **Parent** | JKO-xxxxx（…） |
| **Story Points** | 0.5 |
| **資料庫（PROD DB）** | insurance_pay_db |
| **指派** | 使用者自己 |
| **Priority** | P2 |

### 描述（草稿）
（背景 → 資料庫 → SQL → 執行順序 → 環境範圍 →〔選擇性：表大小/退版/風險〕→ 關聯，見「描述結構」）

確認後跟我說開單我就建立。
```

### 自我檢查清單（公司規定，必附）

DB 異動單一律要附「資料庫異動檢查清單」做自我審查（公司規定）。**建單成功後，自動把清單貼成一則 JIRA comment**：能從票內容推導的題目直接代填，不確定的留 `【待填：xxx】`，第 7 項（後續檢查）留空待上線後填。

**執行方式**：需要貼清單時，**務必先讀 `references/db-change-checklist.md`**（逐題代填邏輯、格式規格），依它把 1.x–6.x 答案整理成 answers JSON，跑產生器腳本 `python scripts/build_checklist_adf.py answers.json` 取得 ADF，再用 `mcp__claude_ai_Atlassian__addCommentToJiraIssue`（**`contentFormat: "adf"`**）貼到剛建立的票。使用者已選「直接貼、留【待填】佔位」，所以建單後直接貼、不需再逐題確認；貼完把代填結果與所有 `【待填】` 項目回報給使用者。

**格式**：答案以「箭頭 `→` ＋ 粗體」與問題區隔；已答核心答案**藍色 `#0055CC`**、`【待填】`**紅色 `#AE2E24`**（顏色需 ADF `textColor`，markdown 做不到，故用 ADF 貼）。

**幾個關鍵點**（詳見參考檔）：
- **代填要依變更類型推理**（加法型 DDL vs 破壞型 DML），備份／Rollback 答案不同，不要寫死。
- **影響筆數（3.1）** 若描述沒有筆數：comment 留 `【待填：影響筆數】`，並**另在對話中**給一句 `SELECT COUNT(*) ... WHERE <與異動相同條件>` 讓使用者自查——**這句查詢 SQL 不進票、不進 comment**。
- **執行時間／避開尖峰（3.4）** 不代填、不標紅、直接留空（取決於實際排程，低流量服務未必在意）；3.4 只填「跑多久」。
- **Review 人員（2.1）** 預設 `@RoyHung`。

## API 呼叫範例

```
mcp__claude_ai_Atlassian__createJiraIssue:
  cloudId: "jkopay.atlassian.net"
  projectKey: "JKO"
  issueTypeName: "Task"
  summary: "[RD3][保險] 調查 SLOW_REQUEST ~30 秒回應模式原因"
  description: "描述內容（Markdown）"
  assignee_account_id: "611e2372c6021e006954b849"
  parent: "JKO-26138"
  additional_fields:
    labels: ["module_paymentApp", "rd3_sprint", "保險"]
    priority:
      name: "P2"
    customfield_10039: 2  # Story Points（classic 欄位，用 10039 非 10016）
```
