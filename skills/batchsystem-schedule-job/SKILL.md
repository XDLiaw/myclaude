---
name: batchsystem-schedule-job
description: Use when creating, adding, or modifying a BatchSystem Schedule Job. Triggers on requests to set up scheduled batch jobs, CronWorkflows, or periodic tasks on the BatchSystem platform.
---

# BatchSystem Schedule Job 建立流程（Step 1 of 3）

需求收集、環境偵測、設定檔產出，引導開發者完成完整的 BatchSystem Schedule Job 串接。

---

## 語言規則

所有輸出使用**繁體中文**。技術術語（欄位名、指令、YAML key、JSON key）保留英文原文。

---

## Step 1：開場導覽

每次被呼叫，先顯示以下訊息：

```
📋 BatchSystem Schedule Job 建立流程

本流程共 3 個步驟：

  Step 1（目前）：需求收集與環境偵測
  Step 2：App 程式碼建立（/batchsystem-job-scaffold）
  Step 3：GitOps 設定建立（/batchsystem-gitops-scaffold）

每個步驟完成後會自動引導到下一步。
```

---

## Step 2：Round 1 — 核心資訊收集（4 題）

**一題一題問，等使用者回答後再問下一題。** 不要一次列出所有問題。

**問題 1：**
```
請問你是哪一個 team？

  (a) rd1
  (b) rd2
  (c) rd3
  (d) foundation
  (x) 自行輸入

請選擇或輸入 team 名稱：
```

收到回答後：

**問題 2：**
```
專案名稱？（kebab-case，例：jkopay-insurance）

  (x) 自行輸入

請輸入專案名稱：
```

收到回答後：

**問題 3：**

先自動推導建議路徑：`/Users/{username}/source_code/jkopay/{project}`（從當前工作目錄推導）。

```
Job 的 App 專案路徑？

  (a) {推導的建議路徑}（建議）
  (x) 自行輸入

請選擇或輸入路徑：
```

收到回答後，驗證路徑是否存在。不存在則確認是否為全新專案。

**問題 4：**

先自動推導建議路徑：從 Additional working directories 或常見路徑推導。

```
GitOps 專案路徑？

  (a) {推導的建議路徑}（建議）
  (x) 自行輸入

請選擇或輸入路徑：
```

收到回答後，進入 Step 3 自動偵測。

---

## Step 3：自動偵測

收到 Round 1 回答後，依序執行以下偵測。過程中不提問，完成後一次展示結果。

### 3.1 技術棧偵測

使用 Glob 工具：
- `{appRepo}/**/*.csproj` 有結果 → `techStack = "dotnet"`
- `{appRepo}/**/pom.xml` 或 `{appRepo}/**/build.gradle` 有結果 → `techStack = "java"`
- 都沒有 → 先繼續後面的偵測，Round 2 再問

### 3.2 模式判斷

使用 Bash 檢查 `{gitopsRepo}/{team}/{project}/kustomize/` 是否存在：
- 目錄**不存在** → `mode = "create"`
- 目錄**存在** → 暫定 Add，Round 2 再確認

### 3.3 既有資源偵測（目錄存在時執行）

1. 使用 Glob 掃描 `{gitopsRepo}/{team}/{project}/kustomize/base/jobs/*-wt.yaml`
   → 取得 WorkflowTemplate 列表

2. 使用 Glob 掃描 `{gitopsRepo}/{team}/{project}/kustomize/base/jobs/*-sj.yaml`
   → 取得 CronWorkflow 列表

3. 使用 Glob 掃描 `{gitopsRepo}/{team}/{project}/kustomize/overlays/`
   → 取得可用環境列表

4. 使用 Read 讀取第一個 `*-sj.yaml`：
   - 取 `spec.workflowSpec.workflowTemplateRef.name` → `sharedTemplateName`

5. 使用 Read 讀取第一個 `*-wt.yaml`：
   - 取 `spec.serviceAccountName` → `serviceAccountName`
   - 取 `spec.templates[0].container.image` → 解析出 `imageRegistry`

### 3.4 偵測結果展示

```
偵測結果：
  技術棧：{techStack 或「未偵測到，Round 2 將詢問」}
  模式：{Create / Add（待確認）}
  App 名稱：{project}
  Namespace：{team}
  現有 WorkflowTemplate：{名稱 ✅ / 未偵測到 ⚠️}
  現有 CronWorkflow：{數量} 個
  可用環境：{環境列表 或「無」}
  共享模板：{sharedTemplateName 或「batchsystem-main-cron-workflow-template（預設）」}
  ServiceAccount：{team}-batchsystem-sa

以上正確嗎？

  (a) 正確，繼續下一步（預設）
  (b) 有需要修正的地方（請說明）

請選擇：
```

---

## Step 4：Round 2 — 依模式提問

確認偵測結果後進入 Round 2。

### Modify 模式判斷

若 3.2 偵測到目錄存在，先確認：

```
偵測到 {team}/{project} 已有現有結構。

你想要：
  (a) 在此 App 新增一個 Job
  (b) 修改現有的 Job

請選擇 (a) 或 (b)
```

- 選 (a) → `mode = "add"`，繼續 Create/Add 問題
- 選 (b) → `mode = "modify"`，進入 Modify 流程

---

### Create / Add 模式問題

**一題一題問，等使用者回答後再問下一題。** 不要一次列出所有問題。每題收到回答後，執行對應的驗證邏輯，確認無誤再進入下一題。

**問題 1：Job 名稱與用途**
```
1. 要建立什麼 Job？

   此名稱會用於 CronWorkflow 命名：{team}-{jobName}-sj
   命名規則：kebab-case（全小寫 + 連字號）

   (x) 自行輸入名稱 + 簡短用途說明
       例：retry-writeoff-job，用於重試沖銷失敗的交易

請輸入 Job 名稱和用途：
```

**命名規則驗證（收到 jobName 後執行）：**
- 必須是 kebab-case（全小寫 + 連字號）
- ❌ 大寫字母（`RetryWriteoffJob`）→ 自動轉換為 `retry-writeoff-job`
- ❌ 底線（`retry_writeoff`）→ 自動轉換為 `retry-writeoff`
- ❌ 空格 → 自動轉換為連字號
- 最終名稱：`{team}-{jobName}-sj`，必須符合 K8s 命名規則（全小寫、字母數字和連字號）

**問題 2：排程時間**
```
2. 排程時間（Cron 格式，Asia/Taipei 時區）：

   (a) 每天凌晨 02:00    → 0 2 * * *
   (b) 每天早上 10:00    → 0 10 * * *
   (c) 每 30 分鐘        → */30 * * * *
   (d) 每月 1 號 08:00   → 0 8 1 * *
   (e) 週一到週五 09:00  → 0 9 * * 1-5
   (x) 自行輸入（cron 表達式或自然語言皆可）

請選擇或輸入排程：
```

**Cron 表達式驗證（收到使用者輸入後執行）：**

1. **位數檢查**：必須是 5 個欄位（分 時 日 月 週）。6 位數含秒是常見錯誤：
   ```
   ❌ "0 0 2 * * *"  → 6 位數（包含秒位）
   ✅ "0 2 * * *"    → 5 位數（Argo Workflow 格式）
   ```
   若偵測到 6 位數，自動移除第一個欄位並提示使用者確認。

2. **數值範圍檢查**：
   - 分鐘: 0-59
   - 小時: 0-23
   - 日: 1-31
   - 月: 1-12
   - 週: 0-7（0 和 7 都是週日）

3. **邏輯衝突檢測**：
   - 同時指定「日」和「週」→ 警告：可能導致預期外行為
   - 不可能的日期（如 `0 2 31 2 *`，2 月無 31 號）→ 警告

4. **自然語言支援**：若使用者輸入自然語言（如「每天凌晨 2 點」），自動轉換：
   - 每天凌晨2點 → `0 2 * * *`
   - 每30分鐘 → `*/30 * * * *`
   - 每月1號早上8點 → `0 8 1 * *`
   - 週一到週五早上9點 → `0 9 * * 1-5`

5. **確認展示**：轉換/驗證後顯示：
   ```
   ✅ Cron 表達式：0 2 * * *
   意義：每天凌晨 02:00（Asia/Taipei）
   ```

**問題 3：jobData**
```
3. jobData（Job 執行參數）：

   (a) 直接貼完整 JSON
       例：{ "jobName": "retryWriteoffJob", "parameter": { "batchSize": 100 } }

   (b) 告訴我 key=value，我幫你組 JSON
       例：jobName=retryWriteoffJob, batchSize=100, startDate=2026-01-01

請選擇 (a) 或 (b) 並提供內容：
```

jobData 解析邏輯：
- 輸入以 `{` 開頭 → 驗證 JSON 格式，若格式錯誤提示修正
- 否則 → 解析 key=value pairs，確認 jobName，組裝標準 JSON 結構

**jobData JSON 驗證（組裝/解析後執行）：**

1. **JSON 語法檢查**：
   - 括號、引號匹配
   - 使用雙引號（❌ 單引號 → 自動修正為雙引號）
   - 無尾隨逗號
   - Key 有引號

2. **結構完整性**：
   - `jobName` 欄位必須存在且非空
   - `parameter` 必須是物件（如果有提供）

3. **jobName 命名檢查**：
   - 提醒：jobName 在 .NET SDK 中會被轉為全小寫作為 DI serviceKey
   - 提醒：確認 .NET code 中 `AddKeyedScoped<IJob, {ClassName}>("{jobname}")` 的 key 一致

4. **base64 編碼安全**：
   - **必須使用 `echo -n`**（避免換行符被編碼進去）
   - 編碼後立即解碼驗證：
     ```bash
     ENCODED=$(echo -n '{"jobName":"xxx","parameter":{}}' | base64)
     echo $ENCODED | base64 --decode  # 驗證能還原
     ```

**問題 4：各環境是否相同**
```
4. 各環境的 schedule 和 jobData 是否相同？

   (a) 相同，全部用同一份（預設）
   (b) 不同，我要分環境設定

請選擇：
```

若選 (b)，針對每個環境（sit/uat/prod）分別收集 schedule 和 jobData。

**問題 5：要產哪些環境的 overlay**
```
5. 要產出哪些環境的 overlay？

   (a) sit uat prod（全部，預設）
   (b) sit uat
   (c) sit
   (d) prod
   (x) 自行輸入組合（例：sit prod）

請選擇：
```

**問題 6：多實例（Sharding）**
```
6. 這個 Job 每次執行時，需要同時跑多個 Pod 分工處理嗎？

   例如：100 萬筆資料，拆成 5 個 Pod 各處理 20 萬筆

   (a) 不需要，單一 Pod 跑完就好（預設，大多數 Job 選這個）
   (b) 需要，我想要分成多個 Pod 同時跑
   (x) 自行輸入 Pod 數量（例：5）

   選 (b) 後會再詢問 Pod 數量。

請選擇：
```

**問題 7：進階選項**
```
7. 進階選項：

   (a) 全部使用預設值（預設）
       - Container：requests 256Mi/100m，limits 512Mi/500m
       - 超時時間：不設
       - 失敗重試：不重試
       - 暫停（suspend）：不暫停
   (b) 我要調整部分設定

   選 (b) 後會逐項詢問要調整哪些。

請選擇：
```

若選 (b)，逐項詢問：

```
要調整哪些項目？（可多選）

  (a) Container 資源限制
  (b) Job 超時時間（activeDeadlineSeconds）
  (c) 失敗自動重試（retryStrategy）
  (d) 新建的 CronWorkflow 先暫停（suspend）
  (x) 自行輸入

請選擇要調整的項目：
```

**技術棧未偵測到時**，在此加問：
```
偵測不到技術棧，請問你的 App 使用什麼語言/框架？

  (a) .NET（C#）（預設）
  (b) Java
  (x) 其他（請說明）

請選擇：
```

---

### Modify 模式問題

1. 列出所有現有 CronWorkflow（從 `*-sj.yaml` 檔案掃描），讓使用者選擇
2. 使用 Read 讀取選中的 CronWorkflow，展示現有設定
3. 詢問要修改哪些項目：

```
請選擇要修改的項目（可多選）：

  (a) schedule（排程時間）
  (b) jobData（執行參數）
  (c) concurrencyPolicy（並發策略）
  (d) suspend（暫停 / 啟用）
  (e) 資源限制（resources）
  (x) 自行說明要修改的內容

請選擇：
```

4. 針對選擇的項目收集新值

---

## Step 5：前置條件檢查

收集完所有資訊後，執行以下檢查並顯示提醒（只警告，不負責建立）：

| 項目 | 檢查方式 | 提醒訊息 |
|------|---------|---------|
| 共享模板 | 使用 Grep 在 `{gitopsRepo}/foundation/` 搜尋 `batchsystem-main-cron-workflow-template` | ⚠️ 請確認 Platform 團隊已為 `{team}` namespace 部署共享模板 |
| ServiceAccount | 使用 Glob 檢查 `{gitopsRepo}/foundation/batchsystem/rbac/{team}/` 是否存在 | ⚠️ 請確認 `{team}-batchsystem-sa` 已建立 |
| K8s Secret（SIT/UAT） | 固定提醒 | 📝 請確認 `{env}-{project}-secret` 已建立 |
| Vault path（PROD） | 固定提醒 | 📝 請確認 Vault path `secret/data/prod/{team}/app/{project}` 已配置 |
| ArgoCD | 固定提醒 | 📝 請確認 ArgoCD 已配置監控 `gitops/{team}/{project}` 路徑 |

顯示格式：
```
📋 前置條件檢查

  ✅ 共享模板已偵測到
  ⚠️ 未找到 ServiceAccount 設定，請確認 rd3-batchsystem-sa 已建立
  📝 請確認 sit-jkopay-insurance-secret 已建立（SIT K8s Secret）
  📝 請確認 Vault path secret/data/prod/rd3/app/jkopay-insurance 已配置（PROD）
  📝 請確認 ArgoCD 已配置監控 gitops/rd3/jkopay-insurance 路徑
```

---

## Step 6：jobDataBase64 計算

針對每個環境，使用 Bash 計算 base64：

```bash
echo -n '{jobData JSON 字串（不含換行）}' | base64
```

---

## Step 7：產出設定檔

將所有收集與偵測的資訊寫入 `{appRepo}/.batchsystem-job-config.json`。

完整 schema：

```json
{
  "mode": "create | add | modify",
  "team": "rd3",
  "project": "jkopay-insurance",
  "appName": "jkopay-insurance",
  "jobName": "retry-writeoff-job",
  "techStack": "dotnet | java",
  "dotnetProjectName": "JKOPay.Insurance.Job",
  "schedule": {
    "sit": "*/30 * * * *",
    "uat": "0 10 * * *",
    "prod": "0 10 * * *"
  },
  "jobData": {
    "sit": { "jobName": "retryWriteoffJob", "parameter": { "batchSize": 100 } },
    "uat": { "jobName": "retryWriteoffJob", "parameter": { "batchSize": 500 } },
    "prod": { "jobName": "retryWriteoffJob", "parameter": { "batchSize": 1000 } }
  },
  "jobDataBase64": {
    "sit": "eyJqb2JOYW1lIjoi...",
    "uat": "eyJqb2JOYW1lIjoi...",
    "prod": "eyJqb2JOYW1lIjoi..."
  },
  "environments": ["sit", "uat", "prod"],
  "sharding": false,
  "instanceCount": 1,
  "concurrencyPolicy": "Forbid",
  "resources": {
    "requests": { "memory": "256Mi", "cpu": "100m" },
    "limits": { "memory": "512Mi", "cpu": "500m" }
  },
  "activeDeadlineSeconds": null,
  "retryStrategy": null,
  "suspend": false,
  "paths": {
    "appRepo": "/path/to/app-repo",
    "gitopsRepo": "/path/to/gitops",
    "gitopsAppBase": "/path/to/gitops/rd3/jkopay-insurance/kustomize/base",
    "gitopsOverlays": "/path/to/gitops/rd3/jkopay-insurance/kustomize/overlays"
  },
  "detected": {
    "hasWorkflowTemplate": true,
    "workflowTemplateName": "rd3-jkopay-insurance-argojob-wt",
    "sharedTemplateName": "batchsystem-main-cron-workflow-template",
    "serviceAccountName": "rd3-batchsystem-sa",
    "imageRegistry": "asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository",
    "overlayStructure": "overlays/{env}/idc/jobs/"
  }
}
```

### 推導規則（不需詢問使用者）

| 欄位 | 推導方式 |
|------|---------|
| `namespace` | 等於 `team` |
| `serviceAccountName` | `{team}-batchsystem-sa` |
| `workflowTemplateName` | `{team}-{project}-argojob-wt` |
| `sharedTemplateName` | 從現有 CronWorkflow 偵測；未偵測到 → 預設 `batchsystem-main-cron-workflow-template` |
| `imageRegistry` | 從現有 WorkflowTemplate 偵測；未偵測到 → 預設 `asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository` |
| `overlayStructure` | 從現有 overlays 結構偵測；未偵測到 → 預設 `overlays/{env}/idc/jobs/` |
| `gitopsAppBase` | `{gitopsRepo}/{team}/{project}/kustomize/base` |
| `gitopsOverlays` | `{gitopsRepo}/{team}/{project}/kustomize/overlays` |
| `jobDataBase64` | 每個環境的 jobData JSON 各算一份 base64 |
| `instanceCount` | sharding=false → `1`；sharding=true → 使用者指定的數量 |
| `dotnetProjectName` | **由 Step 2（batchsystem-job-scaffold）填入**，Step 1 不需設定；techStack=java 時留空 |

---

## Step 8：Handoff

設定檔寫入完成後顯示：

```
✅ Step 1 完成！設定檔已寫入 .batchsystem-job-config.json

📄 設定摘要：
  模式：{mode}
  Team：{team}
  專案：{project}
  Job 名稱：{jobName}
  技術棧：{techStack}
  環境：{environments}
  Sharding：{sharding}

接下來進入 Step 2：App 程式碼建立
正在呼叫 /batchsystem-job-scaffold ...
```

然後自動呼叫 `/batchsystem-job-scaffold`。
