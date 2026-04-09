---
name: elastalert-manager
description: 協助新增或調整 ElastAlert 告警規則。當需要新增告警、修改告警條件、建立 job 未執行監控、或設定錯誤通知時使用。自動查詢現有告警慣例、驗證 Elasticsearch query 和 Kibana Link 正確性。支援 frequency、flatline 等 rule type。
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
  - mcp__playwright__browser_fill_form
  - mcp__playwright__browser_wait_for
---

# ElastAlert Manager Skill

協助使用者新增或調整 ElastAlert 告警規則，自動查詢慣例、生成 YAML、驗證 query 正確性。

## 核心原則

1. **主動詢問** — 收集所有必要資訊後才生成告警檔案
2. **參考慣例** — 從同目錄/同 team 的現有告警中提取 slack webhook、opsgenie key、命名慣例
3. **驗證正確性** — 用 Playwright 在 Kibana 上驗證 query 和 link
4. **說明邏輯** — 產出後解釋每個設定的原因和效果

## 告警規則存放位置

```
elastalert/deployments/ansible/inventories/{env}/group_vars/common/files/elastalert/rules/{team}/{domain}/
```

### 環境對照

| 環境 | 目錄 | 檔名前綴 | Kibana |
|------|------|----------|--------|
| PROD | `prod/` | (無) | `kibana.jkopay.com` |
| UAT | `sit/` | `uat_` | `sit-kibana.jkopay.app` |
| SIT | `sit/` | (無) | `http://172.16.12.138:5601` |

**注意**: UAT 和 SIT 的告警都放在 `sit/` 目錄下，UAT 以 `uat_` 為檔名前綴區分。

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "新增告警" / "新增 alert"
- "監控 job 有沒有跑"
- "設定錯誤通知"
- "調整告警條件"
- "修改 alert 的 timeframe"
- "新增 flatline 監控"

## 操作流程

### 步驟 1：確認告警類型

詢問使用者需要哪種告警：

| 類型 | 用途 | 適用場景 |
|------|------|----------|
| `frequency` | 一段時間內出現 N 次以上符合條件的事件 | 錯誤監控、異常偵測 |
| `flatline` | 一段時間內符合條件的事件低於門檻 | Job 未執行、服務無流量 |

如果使用者描述的是「job 沒有跑要通知」→ 選 `flatline`。
如果使用者描述的是「出現某種錯誤要通知」→ 選 `frequency`。

### 步驟 2：收集必要資訊

根據告警類型，逐步詢問以下資訊（可以一次詢問多項）：

#### 共同資訊

| # | 資訊 | 說明 | 範例 |
|---|------|------|------|
| 1 | **告警名稱/用途** | 要監控什麼 | "DailyTransactionReportJob 沒跑要通知" |
| 2 | **Log 特徵** | 正常/異常時 log 的內容 | `msg: "Start run [XXXJob]"` |
| 3 | **Elasticsearch index** | log 寫在哪個 index | 建議先查同 team 現有告警 |
| 4 | **環境** | PROD / UAT / SIT | 可多選 |
| 5 | **通知對象** | Slack 要 tag 誰 | 參考同 team 告警 |
| 6 | **Team / Domain** | 放在哪個目錄下 | `rd3/insurance` |

#### frequency 額外資訊

| # | 資訊 | 說明 |
|---|------|------|
| 7 | **num_events** | 觸發門檻（N 次） |
| 8 | **timeframe** | 在多長時間內 |
| 9 | **realert** | 重複告警冷卻時間 |

#### flatline 額外資訊

| # | 資訊 | 說明 |
|---|------|------|
| 7 | **threshold** | 低於幾筆觸發（通常設 1） |
| 8 | **預期執行頻率** | Job 多久跑一次、預定什麼時間跑 |
| 9 | **timeframe 計算** | 根據執行頻率 + buffer 計算（見下方） |

### 步驟 3：查詢現有慣例

在生成檔案前，**必須**查詢同 team/domain 的現有告警，提取：

```bash
# 查詢同目錄的現有告警
Glob: **/prod/**/rules/{team}/{domain}/*.yaml

# 從現有告警提取：
# 1. Slack webhook URL
# 2. OpsGenie API key 和設定
# 3. 檔案開頭的人員註解格式
# 4. alert_text 的風格
# 5. include 欄位清單
# 6. index pattern
```

### 步驟 4：生成告警 YAML

根據收集的資訊和慣例生成 YAML 檔案。

#### flatline 的 timeframe 計算邏輯

對於 flatline 類型的告警，timeframe 的計算需要特別注意：

**目標**：讓 flatline 在「Job 應該跑但沒跑」的時間點觸發，而非提前或延後太多。

**計算公式**：
```
timeframe = 執行間隔 + 啟動 buffer

範例（每日 04:30 執行的 Job，啟動需 1~3 分鐘）：
timeframe = 24 小時 + 15 分鐘 = 1455 分鐘

原理：
- 前一天 04:30 的 log 在今天 04:45 離開 window
- 如果今天 04:33 前 job 有跑，新 log 在 window 內 → 不告警
- 如果沒跑 → window 內 0 筆 → ~04:45 告警
```

**重要**：timeframe 的數值如果不直覺（如 1455 分鐘），必須加上註解說明計算邏輯。

#### flatline 的 realert 設定

flatline 沒有 realert 會導致每次 rule evaluation（預設每 5 分鐘）都重複告警。
即使使用者說「不需要 realert」，實際上應該設定 `realert: hours: 24`（一天告警一次）。
需要向使用者解釋 realert 在 flatline 中的作用是「抑制重複通知」而非「重新告警」。

### 步驟 5：驗證 Query 正確性

**必須**用 Playwright 開啟 Kibana 驗證以下兩項：

#### 5a. 驗證 ElastAlert filter query

在 Kibana Discover 上執行告警中的 query，確認：
- 語法正確（無 error）
- 能查到預期的 log（或確認目前查不到是合理的，如 job 暫停中）

```
導航到 Kibana Discover，使用告警的 index 和 query 搜尋
確認結果數量和內容是否符合預期
```

#### 5b. 驗證 Kibana Link

開啟告警中的 Kibana Link URL，確認：
- 能正常載入
- Query 正確顯示在搜尋欄
- Index 正確
- 時間範圍合理

**注意**：Kibana 是 SPA，從同一個 Discover 頁面切換 hash 可能不會更新 query。
需要先導航到 `kibana.jkopay.com/s/rd3/app/home`，再導航到目標 URL。

### 步驟 6：輸出設定說明

告警建立後，必須輸出一份設定摘要，包含：

```markdown
### 設定摘要

| 項目 | 值 |
|------|------|
| **Type** | flatline / frequency |
| **Index** | xxx |
| **Filter** | query 內容 |
| **Threshold / num_events** | 值和意義 |
| **Timeframe** | 值 + 計算邏輯 |
| **Realert** | 值 + 效果說明 |
| **通知管道** | Slack + OpsGenie Px |

### 觸發條件說明
（用白話說明什麼情況下會觸發告警）

### Kibana 驗證結果
- Filter query: [驗證結果]
- Kibana link: [驗證結果]
```

## YAML 範本

### frequency 範本（錯誤監控）

```yaml
# 人員註解（從同 team 現有告警複製）

name: {domain}_{alert_name}
type: frequency
index: {index_pattern}
num_events: {threshold}
timeframe:
  minutes: {timeframe}
realert:
  minutes: {realert}
filter:
  - query:
      query_string:
        query: "{elasticsearch_query}"
include: ["service", "msg", "level", "traceId", "correlationId", "className"]
alert_subject: "{alert_subject}"
alert_subject_args:
  - service
  - level
alert_text_type: alert_text_only
alert_text: |
  {alert_message}
  [{0}] {1} occurred!
  {2}
  to : {slack_mentions}
  Kibana Link: <{kibana_link} | Log Link >
  message:
  {3}
alert_text_args:
  - service
  - level
  - "@timestamp"
  - msg
alert:
  - "slack"
  - "opsgenie"
slack:
slack_webhook_url: "{slack_webhook}"
opsgenie:
opsgenie_details:
  owner: "{owner_email}"
opsgenie_key: "{opsgenie_key}"
opsgenie_message: "{opsgenie_message}"
opsgenie_priority: "{priority}"
opsgenie_tags: ["{env}", "jkopay", "{domain}", "{tags}"]
```

### flatline 範本（Job 未執行監控）

```yaml
# 人員註解（從同 team 現有告警複製）

name: {domain}_{job_name}_not_running
type: flatline
index: {index_pattern}
threshold: 1
# {timeframe 計算說明}
timeframe:
  minutes: {calculated_timeframe}
realert:
  hours: 24
filter:
  - query:
      query_string:
        query: "{elasticsearch_query}"
include: ["service", "msg", "level", "traceId", "correlationId", "className"]
alert_subject: "{alert_subject}"
alert_subject_args:
  - service
  - level
alert_text_type: alert_text_only
alert_text: |
  {alert_message}
  to : {slack_mentions}
  Kibana Link: <{kibana_link} | Log Link >
alert:
  - "slack"
  - "opsgenie"
slack:
slack_webhook_url: "{slack_webhook}"
opsgenie:
opsgenie_details:
  owner: "{owner_email}"
opsgenie_key: "{opsgenie_key}"
opsgenie_message: "{opsgenie_message}"
opsgenie_priority: "{priority}"
opsgenie_tags: ["{env}", "jkopay", "{domain}", "{tags}"]
```

**flatline 注意事項**：
- flatline 觸發時**沒有匹配事件**，所以 `alert_text` 中不能使用 `{0}` `{1}` 等 `alert_text_args` 佔位符
- 不需要 `alert_text_args` 區塊
- `alert_text` 應該是純靜態訊息，描述排程資訊和檢查方向

## 常見 Index Pattern

以下是已知的 index pattern（根據環境不同有不同前綴）：

| Team/Domain | PROD Index | 說明 |
|-------------|-----------|------|
| rd3/insurance API | `rd3-prod-jkopay-insurance-api-%Y.%m.%d*` | 保險 API 服務 |
| rd3/insurance Argo Job | `rd3-prod-rd3-jkopay-insurance-argojob-wt-*` | 保險 Argo Workflow Job |
| rd3/cobranded | `prod-jkopay-cobranded-*` | 聯名卡服務 |
| rd3/campaign-ap | `prod-jkopay-campaign-ap-%Y.%m.%d*` | 活動平台 |

**重要**：Index pattern 可能隨時間變動，建議優先從同 team 的現有告警中查找，或用 Playwright 到 Kibana 確認。

## Kibana 環境

| 環境 | URL | 空間 |
|------|-----|------|
| PROD | `https://kibana.jkopay.com` | `/s/rd3/` |
| UAT | `https://sit-kibana.jkopay.app` | `/s/rd3/` |
| SIT | `http://172.16.12.138:5601` | `/s/rd3/` |

## 注意事項

1. **先查慣例再生成** — 不同 team/domain 有不同的 slack webhook、opsgenie key、命名風格
2. **驗證是必要步驟** — 每次建立或修改告警後，必須用 Playwright 驗證 query 和 Kibana link
3. **Kibana SPA 注意** — 驗證 Kibana link 時，先導航到 home 頁面再開啟目標 URL，避免 SPA cache 問題
4. **flatline 無事件** — flatline 類型觸發時沒有匹配事件，alert_text 不能用佔位符
5. **timeframe 要加註解** — 非直覺的數值（如 1455 分鐘）必須加上計算邏輯註解
6. **realert 必要性** — flatline 必須設定 realert，否則會持續重複告警；向使用者解釋這是「抑制重複」非「重新告警」
7. **多環境注意** — UAT 和 SIT 共用 `sit/` 目錄，UAT 檔名加 `uat_` 前綴，index pattern 也不同
