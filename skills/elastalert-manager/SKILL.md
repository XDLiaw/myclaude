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

**CRITICAL — 公司有兩套完全獨立的 ElastAlert，慣例完全相反。動手前一定要先判斷是哪一套。**

### 先判斷：電支（jkopay）還是金科（jkos）

依**服務**判斷，不是依團隊：

| 體系 | 服務範例 | 判斷依據 |
|------|---------|---------|
| **電支 jkopay** | `jkopay-insurance`（保險）、`jkopay-ebpp`（繳費）、campaign、coupon、marketing、cobranded | repo 在 `gitlab.jkopay.app` |
| **金科 jkos** | `jkos-donation`（捐款）、`jkos-svc-transporthub`（叫車） | repo 在 `gitlab.jkos.app` |

不確定就問使用者，或用 `glab api --hostname <host> "projects?search=<service>"` 兩邊各查一次。

### 電支（jkopay）— K8s + Kustomize + Argo CD

```
gitlab.jkopay.app → devops/gitops
sre/elastalert/kustomize/overlays/{prod,sit}/idc/rules/{team}/{domain}/
```

本機通常已 clone 在 `C:\Workspace\gitops`。

| 環境 | 目錄 | 檔名前綴 | Kibana | ES |
|------|------|----------|--------|-----|
| PROD | `overlays/prod/idc/rules/` | (無) | `log-kibana-gcp.jkopay.com` | GCP |
| UAT | `overlays/sit/idc/rules/` | `uat_` | `log-kibana-gcp.jkopay.app` | GCP |
| SIT | `overlays/sit/idc/rules/` | (無) | `log-kibana-gcp.jkopay.app` | GCP |

**index 命名（2026-11 起，不帶日期、不開 `use_strftime_index`）**：

- k8s：`logs-{ns}-{env}-{app}`
- Swarm：`logs-swarm-{env}-{service}`
- VM：`logs-vm-{env}-*`

### 金科（jkos）— VM + Jenkins + Ansible

```
gitlab.jkos.app → monitoring/service-check
elastalert/deployments/ansible/inventories/{prod,sit}/group_vars/common/files/elastalert/rules/{team}/{domain}/
```

| 環境 | 目錄 | Kibana | ES |
|------|------|--------|-----|
| PROD | `inventories/prod/` | `kibana.jkos.com` | IDC（見同路徑的 `config.yaml`） |
| SIT | `inventories/sit/` | `sit-kibana.jkos.app` | IDC |

**index 命名（維持舊式，要帶日期、要開 `use_strftime_index: true`）**：`prod-jkos-donation-*`、`prod-jkos-svc-transporthub-*`、`sit-jkos-donation-*`。

**不要**把電支的 GCP data stream 命名套到金科——金科的 log 不進 GCP ES（`log-es-gcp.jkopay.com` 是 jkopay 專用），套了會查不到任何資料、靜默漏報。

### 背景（2026-11-25）

SRE 把電支的 Production ElastAlert 從 IDC ES 切到 GCP ES，IDC Elasticsearch / Kibana 於 12/3 下架。**金科不在下架範圍**，維持原樣。所以兩套的 host 與 index 慣例從此分岔，別再混用。

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
# 電支：Glob C:\Workspace\gitops\sre\elastalert\kustomize\overlays\prod\idc\rules\{team}\**\*.yaml
# 金科：glab api --hostname gitlab.jkos.app \
#   "projects/monitoring%2Fservice-check/repository/tree?recursive=true&per_page=100&path=<rules 路徑>"

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
需要先導航到該環境 Kibana 的 `/s/rd3/app/home`，再導航到目標 URL。

**data view id 不可跨環境沿用**：GCP Kibana 的 data view 是重建的，id 與舊 IDC 完全不同，且 URL 的 `filters` 區段內也有 `index:<uuid>`，同一條規則可能出現多次。取得 id 的方式——登入該 Kibana 後執行：

```js
// 在 Kibana 頁面的 console / browser_evaluate
await (await fetch('/s/rd3/api/data_views', {headers:{'kbn-xsrf':'true'}})).json()
```

（PROD ES 帳號是 `editor`，讀不到 `.kibana*` 系統索引，所以不能走 ES API 撈，只能從 Kibana 網頁取。）

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

### 電支（GCP data stream，不帶日期）

| Team/Domain | PROD Index | 說明 |
|-------------|-----------|------|
| rd3/insurance API | `logs-rd3-prod-jkopay-insurance-api` | 保險 API 服務 |
| rd3/insurance Argo Job | `logs-rd3-prod-rd3-jkopay-insurance-argojob-wt` | 保險 Argo Workflow Job |
| rd3/api-gateway | `logs-rd3-prod-jkopay-api-gateway*` | API Gateway |

### 金科（舊式，帶日期 + `use_strftime_index: true`）

| Team/Domain | PROD Index | 說明 |
|-------------|-----------|------|
| rd3/donation | `prod-jkos-donation-*` | 捐款 |
| rd3/transporthub | `prod-jkos-svc-transporthub-*` | 叫車 |

**重要**：Index pattern 可能隨時間變動，建議優先從同 team 的現有告警中查找，或直接用對應的 `elasticsearch` / `elasticsearch-prod` MCP 查一次確認有資料（金科的 log 不在這兩座 GCP ES 上，要改用 Kibana 網頁確認）。

## Kibana 環境

### 電支（jkopay）

| 環境 | URL | 空間 |
|------|-----|------|
| PROD | `https://log-kibana-gcp.jkopay.com` | `/s/rd3/` |
| SIT / UAT | `https://log-kibana-gcp.jkopay.app` | `/s/rd3/` |

舊的 `kibana.jkopay.com`、`sit-kibana.jkopay.app` 預計 2026-12-03 下架，不要再用。

### 金科（jkos）

| 環境 | URL | 空間 |
|------|-----|------|
| PROD | `https://kibana.jkos.com` | `/s/rd3/` |
| SIT | `https://sit-kibana.jkos.app` | `/s/rd3/` |

## 注意事項

0. **先判斷電支還是金科** — 兩套 repo、佈署方式、ES、Kibana、index 命名全部不同，搞錯會放錯 repo 且規則永遠命中 0 筆（靜默漏報）。見「告警規則存放位置」。
1. **先查慣例再生成** — 不同 team/domain 有不同的 slack webhook、opsgenie key、命名風格
2. **驗證是必要步驟** — 每次建立或修改告警後，必須用 Playwright 驗證 query 和 Kibana link
3. **Kibana SPA 注意** — 驗證 Kibana link 時，先導航到 home 頁面再開啟目標 URL，避免 SPA cache 問題
4. **flatline 無事件** — flatline 類型觸發時沒有匹配事件，alert_text 不能用佔位符
5. **timeframe 要加註解** — 非直覺的數值（如 1455 分鐘）必須加上計算邏輯註解
6. **realert 必要性** — flatline 必須設定 realert，否則會持續重複告警；向使用者解釋這是「抑制重複」非「重新告警」
7. **多環境注意** — UAT 和 SIT 共用 `sit/` 目錄，UAT 檔名加 `uat_` 前綴，index pattern 也不同
