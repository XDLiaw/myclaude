---
name: argo-workflow-integrator
description: 協助團隊成員快速建立和配置 Argo Workflow 的 WorkflowTemplate 和 Schedule Job。當需要新增 batch job、建立定時任務、配置 CronWorkflow、或整合 Argo Workflow 時使用。支援全新專案和既有專案新增 job 兩種情境。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Argo Workflow Integrator Skill

自動化建立和配置 Argo Workflow 相關的 YAML 檔案，包含 WorkflowTemplate 和 Schedule Job。

## 核心功能

1. **全新專案整合** - 建立完整的 wt + sj 配置
2. **既有專案新增 Job** - 僅新增 Schedule Job
3. **環境配置生成** - 自動產生 SIT/UAT/PROD 的 overlay patches
4. **參數驗證** - 確保命名規則、格式正確性
5. **自動更新 kustomization.yaml** - 維護資源清單

## 重要：TODO 註解保留規則

**生成 YAML 檔案時，必須保留 templates.md 範本中的所有 TODO 註解和說明性註解。**

這些 TODO 是供後續維護人員參考的重要標記，即使變數已被替換為實際值，TODO 仍須保留。範例：

```yaml
# ✅ 正確：保留 TODO 註解
name: rd3-monthly-fee-request-report-job-sj
namespace: rd3 #TODO: 請修改team name

# ❌ 錯誤：省略 TODO 註解
name: rd3-monthly-fee-request-report-job-sj
namespace: rd3
```

生成檔案時請嚴格對照 [templates.md](./templates.md) 中的範本，確保每個 TODO 和註解都被保留。

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "幫我新增一個 batch job"
- "我要建立 Argo Workflow 定時任務"
- "整合 Argo Workflow 到專案"
- "新增 CronWorkflow"
- "建立 WorkflowTemplate"
- "配置排程任務"

## 操作流程

### 前置收集資訊

在開始建立檔案前，**必須**收集以下資訊：

#### 基本資訊
- **team**: 團隊名稱 (如: rd3, rd1, rd2)
- **app**: 應用程式名稱 (如: jkopay-insurance)
- **job-name**: Job 名稱（僅用於 Schedule Job，如: legacy-retry-write-off）
- **environments**: 目標環境 (預設: sit, 可選: uat, prod)
- **scenario**: 情境類型
  - `new-project`: 全新專案（需要建立 wt + sj）
  - `add-job`: 既有專案新增 job（僅建立 sj）

#### WorkflowTemplate 相關（僅 new-project 需要）
- **service-account**: 格式 `{team}-batchsystem-sa`
- **vault-role**: 格式 `{team}-batchsystem`（提醒使用者需找 SRE 申請）
- **vault-path**: 格式 `secret/data/{env}/{team}/app/{app}`
- **container-image**: Docker image 完整路徑
- **java-command**: Java 啟動指令（包含記憶體設定、Spring profile 等）

#### Schedule Job 相關
- **cron-schedule**: 5 位數 cron 表達式（如: "0 2 * * *"）
- **concurrency-policy**: `Forbid` (預設) | `Allow` | `Replace`
- **job-class-name**: Java job class 名稱（必須與 `getJobName()` 一致）
- **job-parameters**: Job 參數 JSON 物件
- **instance-count**: 需要 sharding 時填寫，預設 "1"

### 資訊確認範例對話

```
Claude: 我將協助您建立 Argo Workflow 配置。請提供以下資訊：

1. 這是全新專案還是既有專案新增 job？
   - 全新專案：需要建立 WorkflowTemplate + Schedule Job
   - 既有專案：僅建立 Schedule Job

2. 基本資訊：
   - Team 名稱: (如 rd3)
   - 應用程式名稱: (如 jkopay-insurance)
   - Job 名稱: (如 legacy-retry-write-off)
   - 目標環境: (預設 sit，可選 sit,uat,prod)

[如果是全新專案]
3. WorkflowTemplate 配置：
   - Container image 路徑: (完整 GCR 路徑)
   - Java 啟動指令: (記憶體設定、Spring profile 等)
   - Vault role 是否已申請？(提醒：格式為 {team}-batchsystem，需找 SRE 申請)

4. Schedule Job 配置：
   - Cron schedule: (5位數，如 "0 2 * * *")
   - Job class 名稱: (Java code 中的 getJobName() 回傳值)
   - Job 參數: (JSON 格式)
   - 並行策略: (Forbid/Allow/Replace，預設 Forbid)
   - 是否需要 Sharding: (需要則提供 instance count)
```

---

## 重要：Overlay 目錄結構偵測

**部分專案的 overlay 目錄已從 `overlays/{env}/` 遷移至 `overlays/{env}/idc/`（為支援多 IDC 部署）。**

在建立檔案前，**必須先偵測目標專案的實際 overlay 結構**：

### 偵測邏輯

```bash
# 檢查 kustomization.yaml 的實際位置
ls {team}/{app}/kustomize/overlays/{env}/kustomization.yaml 2>/dev/null
ls {team}/{app}/kustomize/overlays/{env}/idc/kustomization.yaml 2>/dev/null
```

- 如果 `overlays/{env}/idc/kustomization.yaml` 存在 → 使用 `idc/` 路徑
- 如果 `overlays/{env}/kustomization.yaml` 存在 → 使用直接路徑
- 以下文件中的 `{overlay-dir}` 代表實際偵測到的路徑（`overlays/{env}/` 或 `overlays/{env}/idc/`）

### 路徑對照

| 結構 | Overlay 路徑 | kustomization.yaml 中 base 引用 |
|------|-------------|-------------------------------|
| 舊結構 | `overlays/{env}/` | `../../base` |
| 新結構（idc） | `overlays/{env}/idc/` | `../../../base` |

**注意**：Base 目錄結構不受影響，始終是 `{team}/{app}/kustomize/base/`。

---

## 檔案命名規則

### 重要：Base vs Overlay 檔案命名差異

| 位置 | 檔案類型 | 命名格式 | 範例 |
|------|---------|---------|------|
| **base/jobs/** | WorkflowTemplate | `{team}-{app}-argojob-wt.yaml` | `rd3-jkopay-insurance-argojob-wt.yaml` |
| **base/jobs/** | Schedule Job | `{team}-{job-name}-sj.yaml` | `rd3-fill-disburse-date-sj.yaml` |
| **overlays/{env}/jobs/** | WorkflowTemplate Patch | `{team}-{app}-argojob-wt.patch.yaml` | `rd3-jkopay-insurance-argojob-wt.patch.yaml` |
| **overlays/{env}/jobs/** | Schedule Job Patch | `{team}-{job-name}-sj.patch.yaml` | `rd3-fill-disburse-date-sj.patch.yaml` |

**關鍵規則**：
- ✅ **Base 目錄**：檔名**不含** `.patch`（如 `rd3-job-a-sj.yaml`）
- ✅ **Overlays 目錄**：檔名**必須包含** `.patch`（如 `rd3-job-a-sj.patch.yaml`）

這個命名規則幫助區分：
- Base 檔案：定義資源的基礎配置
- Patch 檔案：覆蓋特定環境的配置


## 建立檔案步驟

### 情境 A: 全新專案（new-project）

#### Step 1: 建立或更新 kustomconfig.yaml

**檔案路徑**: `{team}/{app}/kustomize/overlays/{env}/kustomconfig.yaml`

**檢查邏輯**:
1. 如果檔案不存在，建立完整檔案
2. 如果檔案存在，檢查是否包含 WorkflowTemplate 配置
3. 確保 `kustomization.yaml` 的 `configurations` 區段包含 `kustomconfig.yaml`

**檔案內容**:
```yaml
images:
  - path: spec/templates[]/container/image
    kind: WorkflowTemplate
```

#### Step 2: 建立 Base WorkflowTemplate

**檔案路徑**: `{team}/{app}/kustomize/base/jobs/{team}-{app}-argojob-wt.yaml`

**重要檢查**:
- ✅ `metadata.name` 必須全小寫，格式: `{team}-{app}-argojob-wt`
- ✅ `namespace` 設定為 team 名稱
- ✅ `serviceAccountName` 格式: `{team}-batchsystem-sa`
- ✅ `vault.hashicorp.com/role` 格式: `{team}-batchsystem`
- ✅ Vault path 包含正確的 team 和 app 名稱
- ✅ Container image 路徑正確
- ✅ Command 包含正確的 Java 指令和 workflow 參數

**參考範本**: 使用 `ARGO_WORKFLOW_INTEGRATION_GUIDE.md` 的 "4.1 Base WorkflowTemplate"

#### Step 3: 建立 Overlay WorkflowTemplate Patches

**檔案路徑**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{app}-argojob-wt.patch.yaml`

所有環境都使用 **Vault Sidecar** 注入環境變數。

**重要檢查**:
- ✅ `metadata.labels.environment` 設定正確環境（sit/uat/prod）
- ✅ Vault path 包含正確的環境名稱（`secret/data/{env}/{team}/app/{app}`）
- ✅ `vault.hashicorp.com/agent-inject-secret-env-config` 和 `vault.hashicorp.com/agent-inject-template-env-config` 同步修改
- ✅ Command 包含 `source /vault/secrets/env-config && \`

**參考範本**: `ARGO_WORKFLOW_INTEGRATION_GUIDE.md` 的 "4.2 Overlay WorkflowTemplate"

#### Step 4: 更新 kustomization.yaml (Base)

**檔案路徑**: `{team}/{app}/kustomize/base/kustomization.yaml`

**操作**: 在 `resources` 區段新增:
```yaml
resources:
- jobs/{team}-{app}-argojob-wt.yaml
```

**注意**: 如果已存在則不重複新增

#### Step 5: 更新 kustomization.yaml (Overlays)

**檔案路徑**: `{team}/{app}/kustomize/overlays/{env}/kustomization.yaml`

**操作**: 在 `patches` 區段新增:
```yaml
patches:
- path: jobs/{team}-{app}-argojob-wt.patch.yaml
  target:
    kind: WorkflowTemplate
    name: {team}-{app}-argojob-wt
```

**注意**:
- 如果已存在則不重複新增
- 確保 `configurations` 包含 `kustomconfig.yaml`

---

### 情境 A 和 B 共通: 建立 Schedule Job

#### Step 6: 建立 Base Schedule Job

**檔案路徑**: `{team}/{app}/kustomize/base/jobs/{team}-{job-name}-sj.yaml`

**重要檢查**:
- ✅ `metadata.name` 格式: `{team}-{job-name}-sj`（全小寫）
- ✅ `schedule` 是 5 位數 cron 格式（最小單位是分鐘）
- ✅ `concurrencyPolicy` 設定為使用者指定值或預設 `Forbid`
- ✅ `workflowTemplateRef.name` 保持為 `batchsystem-main-cron-workflow-template`（不加環境前綴）
- ✅ `templateName` 包含環境前綴，格式: `{env}-{team}-{app}-argojob-wt`（PROD 不加前綴）
- ✅ `jobData` 保持為 `placeholder`（避免誤執行）

**Cron Schedule 驗證**:
```
格式: "分 時 日 月 週"
✅ 正確: "0 2 * * *"  (每天凌晨 2:00)
✅ 正確: "*/30 * * * *"  (每 30 分鐘)
❌ 錯誤: "0 0 2 * * *"  (6 位數，包含秒)
```

**參考範本**: `ARGO_WORKFLOW_INTEGRATION_GUIDE.md` 的 "4.3 Base Schedule Job"

#### Step 7: 建立 Overlay Schedule Job Patches

**檔案路徑**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{job-name}-sj.patch.yaml`

**環境前綴規則**:

| 環境 | workflowTemplateRef | templateName | 範例 |
|------|-------------------|--------------|------|
| **SIT** | `sit-batchsystem-main-cron-workflow-template` | `sit-{team}-{app}-argojob-wt` | `sit-rd3-jkopay-insurance-argojob-wt` |
| **UAT** | `uat-batchsystem-main-cron-workflow-template` | `uat-{team}-{app}-argojob-wt` | `uat-rd3-jkopay-insurance-argojob-wt` |
| **PROD** | `batchsystem-main-cron-workflow-template` | `{team}-{app}-argojob-wt` | `rd3-jkopay-insurance-argojob-wt` |

**Sharding 支援**:
如果需要 sharding，在 `workflowTemplateRef.name` 後加 `-sharding` 後綴，並新增參數:
```yaml
arguments:
  parameters:
    - name: instanceCount
      value: "{instance-count}"
```

**jobData 編碼**:
1. 建立 JSON 結構:
```json
{
  "jobName": "{job-class-name}",
  "parameter": {job-parameters}
}
```

2. 使用 bash 進行 base64 編碼:
```bash
echo -n '{json-content}' | base64
```

3. 將編碼結果放入 YAML:
```yaml
- name: jobData
  value: {base64-encoded-string}
```

**重要提醒**:
- ⚠️ `jobName` 必須與 Java code 中 `getJobName()` 回傳值**完全一致**
- ⚠️ `parameter` 物件會被 deserialize 到 Java job 的參數物件
- ⚠️ Base64 編碼時使用 `echo -n` (不含換行符)

**參考範本**: `ARGO_WORKFLOW_INTEGRATION_GUIDE.md` 的 "4.4 Overlay Schedule Job"

#### Step 8: 更新 kustomization.yaml (Base 和 Overlays)

**Base** (`{team}/{app}/kustomize/base/kustomization.yaml`):
```yaml
resources:
- jobs/{team}-{job-name}-sj.yaml
```

**Overlays** (`{team}/{app}/kustomize/overlays/{env}/kustomization.yaml`):
```yaml
patches:
- path: jobs/{team}-{job-name}-sj.patch.yaml
  target:
    kind: CronWorkflow
    name: {team}-{job-name}-sj
```

---

## 驗證配置

**重要：每次產出新檔案或修改現有檔案後，必須自動執行驗證，不需等使用者要求。**

建立完所有檔案後，**必須**對所有目標環境執行驗證：

### 驗證指令

**優先使用 `kubectl kustomize`**（本機已安裝 kubectl 內建 kustomize）：

```bash
# 驗證 kustomize build（優先使用此方式）
kubectl kustomize {team}/{app}/kustomize/overlays/{env}

# 確認新增的資源有正確產出（檢查資源名稱和環境前綴）
kubectl kustomize {team}/{app}/kustomize/overlays/{env} | grep "name: {expected-resource-name}"
```

**如果有安裝獨立的 kustomize + kubeconform**：

```bash
kustomize build {team}/{app}/kustomize/overlays/{env} | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

### 成功輸出範例

```json
{
  "resources": [],
  "summary": {
    "valid": 12,
    "invalid": 0,
    "errors": 0,
    "skipped": 0
  }
}
```

### 常見錯誤處理

| 錯誤訊息 | 可能原因 | 解決方法 |
|---------|---------|---------|
| `metadata.name contains uppercase` | 名稱包含大寫字母 | 確保所有 `metadata.name` 全小寫 |
| `invalid base64` | jobData 編碼錯誤 | 重新使用 `echo -n` 編碼 JSON |
| `invalid cron expression` | cron 格式錯誤 | 確認是 5 位數格式 |
| `image not found` | Image 不存在 | 確認 image 路徑和 tag 正確 |
| `missing required field` | 缺少必填欄位 | 檢查 YAML 結構完整性 |

**處理邏輯**:
1. 如果驗證失敗，顯示錯誤訊息
2. 根據錯誤類型提供修正建議
3. 修正後重新驗證

---

## 輸出摘要

完成所有步驟後，提供清晰的摘要：

### 摘要範例

```markdown
## Argo Workflow 配置完成 ✅

### 建立的檔案

#### Base 檔案
- `{team}/{app}/kustomize/base/jobs/{team}-{app}-argojob-wt.yaml` (WorkflowTemplate)
- `{team}/{app}/kustomize/base/jobs/{team}-{job-name}-sj.yaml` (Schedule Job)

#### SIT Overlay
- `{team}/{app}/kustomize/overlays/sit/jobs/{team}-{app}-argojob-wt.patch.yaml`
- `{team}/{app}/kustomize/overlays/sit/jobs/{team}-{job-name}-sj.patch.yaml`

#### 更新的檔案
- `{team}/{app}/kustomize/base/kustomization.yaml` (新增 resources)
- `{team}/{app}/kustomize/overlays/sit/kustomization.yaml` (新增 patches)
- `{team}/{app}/kustomize/overlays/sit/kustomconfig.yaml` (建立/更新)

### 配置資訊

- **Team**: {team}
- **Application**: {app}
- **Job Name**: {job-name}
- **Environments**: {environments}
- **Cron Schedule**: {cron-schedule}
- **Concurrency Policy**: {concurrency-policy}
- **Java Class**: {job-class-name}
- **Sharding**: {是/否}

### 驗證結果

✅ Kustomize build 成功
✅ Kubeconform 驗證通過
- Valid resources: {count}
- Invalid resources: 0
- Errors: 0

### 下一步

1. **檢查設定**: 確認所有參數正確
2. **Commit 變更**: 提交到 Git repository
3. **部署測試**: 等待 ArgoCD 同步後測試執行
4. **監控日誌**: 在 Micro Admin 後台查看 job 執行狀態

### 重要提醒

⚠️ **Vault Role**: 確認已向 SRE 申請 `{vault-role}` (格式: {team}-batchsystem)
⚠️ **PROD 環境**: 建議在 SIT/UAT 測試完成後，再建立 PROD 配置
⚠️ **jobData 驗證**: 確認 jobName 與 Java code 中 `getJobName()` 回傳值完全一致

### 參考文件

- [Argo Workflow 整合指南](ARGO_WORKFLOW_INTEGRATION_GUIDE.md)
- [Confluence - Argo Job YAML 設定](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1083343059/Argo+Job+yaml)
```

---

## 安全與最佳實踐

### 命名規則強制執行

在建立任何檔案前，驗證所有名稱：

```python
# 偽代碼
def validate_name(name: str) -> bool:
    # 必須全小寫
    if name != name.lower():
        return False
    # 只允許小寫字母、數字、連字號
    if not re.match(r'^[a-z0-9-]+$', name):
        return False
    return True
```

### PROD 環境保護

**重要原則**:
1. 預設不建立 PROD 配置，除非使用者明確要求
2. 建立 PROD 配置前，確認使用者理解風險
3. 提醒使用者先完成 SIT/UAT 測試

**確認對話範例**:
```
⚠️ 您要求建立 PROD 環境配置。

建議流程：
1. 先建立並測試 SIT/UAT 環境
2. 確認功能正常後再建立 PROD 配置

這樣可以避免：
- 測試中的設定被誤帶上 PROD
- 意外執行未經驗證的 job

您確定要現在建立 PROD 配置嗎？(yes/no)
```

### Base64 編碼安全

使用 bash 進行編碼時：
```bash
# ✅ 正確：使用 -n 避免換行符
echo -n '{"jobName":"MyJob"}' | base64

# ❌ 錯誤：包含換行符會導致無效編碼
echo '{"jobName":"MyJob"}' | base64
```

### Vault 配置提醒

每次建立 WorkflowTemplate 時，提醒使用者：

```
⚠️ Vault Role 申請提醒

您的配置需要 Vault role: `{team}-batchsystem`

如果尚未申請，請：
1. 聯繫 SRE 團隊
2. 提供 Team 名稱: {team}
3. 說明用途: Argo Workflow batch job 執行

每個 team 只需申請一次，可供所有 batch job 共用。
```

---

## 參考資源

### 完整整合指南

**本 Skill 的詳細背景知識和完整步驟說明**：

- [ARGO_WORKFLOW_INTEGRATION_GUIDE.md](../../../ARGO_WORKFLOW_INTEGRATION_GUIDE.md)
  - 包含完整的檔案結構說明
  - 詳細的步驟指引（情境 A 和情境 B）
  - 常見問題 FAQ
  - 重要注意事項和最佳實踐

**建議**：當需要深入理解 Argo Workflow 整合流程時，請閱讀此文檔。

### 內嵌資源（本 Skill 使用）

- [templates.md](./templates.md) - YAML 範本庫（本 Skill 用於生成檔案）

### Confluence 官方文件

- [Argo Job YAML 設定](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1083343059/Argo+Job+yaml)
- [WorkflowTemplate 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085800917/Job+WorkflowTemplate)
- [Schedule Job 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085538635/Schedule+Job)

### 範例參考（實際專案）

- `rd3/jkopay-insurance/kustomize/` - 最完整的參考實作
  - 包含完整的 base 和 overlays 配置
  - 多個 Job 範例
  - 不同環境的 patch 設定

### 輔助工具

- [Crontab.guru](https://crontab.guru/) - Cron 表達式驗證（⚠️ 注意 Argo Workflow 只用 5 位數）
- Kustomize - YAML 配置管理工具
- Kubeconform - Kubernetes YAML 驗證工具

---

## 錯誤處理與恢復

### 建立檔案失敗

如果任何步驟失敗：
1. 停止後續步驟
2. 顯示錯誤訊息
3. 提供回滾建議
4. 詢問是否要繼續或取消

### 驗證失敗處理

```markdown
❌ 驗證失敗

錯誤: {error-message}

建議修正:
1. {fix-suggestion-1}
2. {fix-suggestion-2}

已修正的檔案: {file-path}

是否重新驗證？(yes/no)
```

### 回滾機制

如果使用者要求取消：
```markdown
⚠️ 正在回滾變更...

已刪除的檔案:
- {file-1}
- {file-2}

已恢復的檔案:
- {file-3}

回滾完成。
```

---

## 互動式收集資訊範例

### 範例對話流程

```
User: "幫我新增一個 batch job"

Claude (使用此 Skill):
我將協助您建立 Argo Workflow batch job 配置。

首先，請回答幾個問題：

1️⃣ 這是全新專案還是既有專案？
   A. 全新專案 (需要建立 WorkflowTemplate + Schedule Job)
   B. 既有專案 (僅建立 Schedule Job，複用現有 WorkflowTemplate)

User: "既有專案"

Claude:
好的，我將為既有專案新增 Schedule Job。

2️⃣ 基本資訊
   - Team 名稱 (如 rd3):
   - 應用程式名稱 (如 jkopay-insurance):
   - Job 名稱 (如 legacy-retry-write-off):

User: "rd3, jkopay-insurance, daily-settlement"

Claude:
收到！

3️⃣ 目標環境
   預設會建立 SIT 環境配置。

   是否也要建立 UAT/PROD 環境？
   建議: 先建立 SIT 測試，確認無誤後再建立 PROD

User: "先只建立 SIT"

Claude:
好的，僅建立 SIT 環境配置。

4️⃣ Schedule Job 配置
   - Cron schedule (5位數，如 "0 2 * * *" 表示每天凌晨2點):
   - Java job class 名稱 (必須與 getJobName() 一致):
   - Job 參數 (JSON 格式，如 {"batchSize": "1000"}):
   - 並行策略 (Forbid/Allow/Replace，預設 Forbid，建議使用 Forbid):

User: "0 3 * * *, DailySettlementJob, {"date": "today"}, Forbid"

Claude:
完美！讓我確認一下：

📋 配置摘要
- Team: rd3
- App: jkopay-insurance
- Job: daily-settlement
- Environment: SIT
- Schedule: 0 3 * * * (每天凌晨 3:00)
- Job Class: DailySettlementJob
- Parameters: {"date": "today"}
- Concurrency: Forbid

確認無誤後我將開始建立檔案。確認嗎？(yes/no)

User: "yes"

Claude:
開始建立配置...

✅ 建立 Base Schedule Job
✅ 建立 SIT Overlay Patch
✅ 更新 Base kustomization.yaml
✅ 更新 SIT kustomization.yaml
✅ 編碼 jobData (base64)
✅ 驗證配置 (kustomize build + kubeconform)

所有步驟完成！

[顯示完整摘要]
```

---

## 總結

此 Skill 提供：
- ✅ 自動化檔案建立流程
- ✅ 互動式資訊收集
- ✅ 完整的驗證機制
- ✅ 清晰的錯誤處理
- ✅ 環境差異自動處理
- ✅ 安全性檢查（命名、PROD 保護）
- ✅ 詳細的操作摘要

讓團隊成員只需提供簡單的需求描述，即可自動完成所有配置工作。
