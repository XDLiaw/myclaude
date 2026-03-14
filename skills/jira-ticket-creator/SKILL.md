---
name: jira-ticket-creator
description: 協助在 JIRA 上建立票券（Issue）。當需要開 JIRA 單、建立 Task/Story/Bug 時使用。自動查詢專案慣例（Labels、Parent Epic、Sprint），與使用者確認所有欄位後才建立。支援 JKO 及其他 Atlassian 專案。
allowed-tools:
  - Read
  - Glob
  - Grep
  - mcp__atlassian__createJiraIssue
  - mcp__atlassian__searchJiraIssuesUsingJql
  - mcp__atlassian__getJiraIssue
  - mcp__atlassian__editJiraIssue
  - mcp__atlassian__lookupJiraAccountId
  - mcp__atlassian__getVisibleJiraProjects
  - mcp__atlassian__getJiraProjectIssueTypesMetadata
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

使用者隸屬「支付應用模組」，負責以下專案領域：

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
fields: summary, labels, parent, customfield_10016, status

# 查當前 Sprint
JQL: project = {projectKey} AND assignee = 611e2372c6021e006954b849 AND sprint in openSprints() ORDER BY created DESC
fields: summary, customfield_10020

# 查支付應用模組下可用的 Epic（作為 Parent 候選）
JQL: project = {projectKey} AND issuetype = Epic AND status != Done AND labels = module_paymentApp ORDER BY created DESC
fields: summary, status, labels
```

**重點**：
- **預設 Labels**：每張票預設帶上 `module_paymentApp` 和 `rd3_sprint`，這兩個是固定的
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

### 描述（草稿）

> 描述內容...

有需要調整的地方嗎？確認後跟我說開單我就建立。
```

### 步驟 4：等待確認後建立

使用者明確說「開單」、「建立」、「OK」等確認指令後，才呼叫 `mcp__atlassian__createJiraIssue` 建立票券。

建立成功後，回報 Issue Key。

## API 呼叫範例

```
mcp__atlassian__createJiraIssue:
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
    customfield_10039: 2  # Story Points（classic 欄位）
    # ⚠️ 不要用 customfield_10016（那是 "Story point estimate"，next-gen 欄位，JIRA UI 不顯示）
```

## 描述內容撰寫指引

當使用者提供足夠的上下文（如驗證報告、問題描述）時，自動草擬描述內容：

1. **背景** — 問題發生的背景和時間
2. **影響範圍** — 影響的 API、服務或功能
3. **觀察到的現象** — 具體的數據和 LOG 證據
4. **待調查/待處理方向** — 建議的後續動作

描述使用 Markdown 格式撰寫。

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "幫我開一張 JIRA 單"
- "建一張票追蹤這個問題"
- "開 JIRA ticket"
- "建 Task/Story/Bug"
- "幫我在 JKO 專案開單"

## 注意事項

1. **先確認再建立** — 絕對不要未經確認就建票
2. **動態查詢慣例** — Labels 和 Parent 必須從專案歷史票券動態查詢，不同專案有不同慣例
3. **Sprint 處理** — 使用者說「放 backlog」時不要指定 Sprint；需要指定時查詢 openSprints()
4. **描述品質** — 如果有上下文資訊（如驗證報告），主動草擬描述內容
5. **回報結果** — 建立成功後回報 Issue Key
