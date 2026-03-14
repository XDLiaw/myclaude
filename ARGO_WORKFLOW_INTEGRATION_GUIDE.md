# Argo Workflow 串接完整指南

> 本指南整理自 Confluence 官方文件，提供完整的 Argo Workflow 串接步驟。
> 適用於新增 batch job 或全新專案串接 Argo Workflow。

## 目錄
- [一、整體架構理解](#一整體架構理解)
- [二、新增 Job 的完整流程](#二新增-job-的完整流程)
  - [情境 A: 全新專案（需要 wt + sj）](#情境-a-全新專案需要-wt--sj)
  - [情境 B: 既有專案新增 Job（wt 已存在）](#情境-b-既有專案新增-jobwt-已存在)
- [三、重要注意事項](#三重要注意事項)
- [四、完整 YAML 範本](#四完整-yaml-範本)
- [五、參考資源](#五參考資源)

---

## 一、整體架構理解

### 1.1 檔案結構原則
```
{team}/{app}/kustomize/
├── base/                              # 基礎配置（類似 application.yaml）
│   ├── kustomization.yaml
│   └── jobs/
│       ├── {team}-{app}-wt.yaml      # WorkflowTemplate 定義
│       └── {team}-{job}-sj.yaml      # Schedule Job 定義
└── overlays/                         # 環境覆蓋（類似 application-{env}.yaml）
    ├── sit/
    │   ├── kustomization.yaml
    │   ├── kustomconfig.yaml         # Image 客製化配置
    │   └── jobs/
    │       ├── {team}-{app}-wt.patch.yaml
    │       └── {team}-{job}-sj.patch.yaml
    ├── uat/
    └── prod/
```

### 1.2 檔案類型與用途

#### WorkflowTemplate (wt.yaml)
- **用途**: 定義 job 執行容器和配置，相當於 `deployment.yaml`
- **關聯**: 每個 Spring Boot sub-module 對應一份 wt.yaml
- **Kind**: `WorkflowTemplate`

#### Schedule Job (sj.yaml)
- **用途**: 定義排程時間與執行參數，類似 `elastic-job.yaml`
- **關聯**: 每個 job 對應一份 sj.yaml
- **Kind**: `CronWorkflow`

### 1.3 覆蓋原則
- `/overlays` 中的檔案會覆蓋 `/base` 中的重複屬性
- 覆蓋規則與 Spring Boot 的 profile 機制相同
- 建議在 overlay 檔案加上 `.patch` 後綴以示區別

---

## 二、新增 Job 的完整流程

### 情境 A: 全新專案（需要 wt + sj）

當你要為一個新的 Spring Boot sub-module 建立 Argo Workflow 配置時，需要建立完整的 wt 和 sj 檔案。

#### Step 1: 建立 kustomconfig.yaml

**檔案位置**: `{team}/{app}/kustomize/overlays/{env}/kustomconfig.yaml`

**檔案內容**:
```yaml
images:
  - path: spec/templates[]/container/image
    kind: WorkflowTemplate
```

**更新 kustomization.yaml**:
在 `{team}/{app}/kustomize/overlays/{env}/kustomization.yaml` 中新增:
```yaml
configurations:
- kustomconfig.yaml
```

**說明**:
- 此配置讓 Kustomize 知道如何處理 WorkflowTemplate 的 image 欄位
- 每個環境都需要建立（sit, uat, prod）

---

#### Step 2: 建立 Base WorkflowTemplate

**檔案位置**: `{team}/{app}/kustomize/base/jobs/{team}-{app}-wt.yaml`

**命名規則**: `{team name}-{app-name}-wt.yaml`

**範本**: 見 [四、完整 YAML 範本 - Base WorkflowTemplate](#41-base-workflowtemplate)

**必填 TODO 檢查清單**:

- [ ] `metadata.name`: 格式 `{team}-{app}-wt`（**全小寫，不可有大寫**）
- [ ] `metadata.namespace`: 修改為你的 team name（如 rd3）
- [ ] `metadata.annotations.batchsystem/project`: 專案名稱（建議用 git repo 名稱）
- [ ] `spec.serviceAccountName`: 格式 `{team}-batchsystem-sa`
- [ ] `vault.hashicorp.com/role`: 格式 `{team}-batchsystem`（**需找 SRE 申請新 role**）
- [ ] `vault.hashicorp.com/agent-inject-secret-env-config`: Vault 路徑 `secret/data/sit/{team}/app/{app}`
- [ ] `vault.hashicorp.com/agent-inject-template-env-config`: 同步修改 Vault 路徑
- [ ] `container.image`: 實際的 Docker image 路徑（可參考 kustomization.yaml 的 images）
- [ ] `container.command`: 實際執行指令（可參考原 Dockerfile 的 ENTRYPOINT）

**更新 kustomization.yaml**:
在 `{team}/{app}/kustomize/base/kustomization.yaml` 的 `resources` 區段新增:
```yaml
resources:
- jobs/{team}-{app}-wt.yaml
```

---

#### Step 3: 建立 Overlay WorkflowTemplate Patches

**檔案位置**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{app}-wt.patch.yaml`

**命名規則**: `{team name}-{app-name}-wt.patch.yaml`

**範本**: 見 [四、完整 YAML 範本 - Overlay WorkflowTemplate](#42-overlay-workflowtemplate)

**必填 TODO 檢查清單**:

- [ ] `metadata.labels.environment`: 修改為實際環境（sit/uat/prod）
- [ ] `vault.hashicorp.com/agent-inject-secret-env-config`: 更新環境路徑（如 `secret/data/{env}/{team}/app/{app}`）
- [ ] `vault.hashicorp.com/agent-inject-template-env-config`: 同步修改 Vault 路徑
- [ ] `container.image`: 確認 image 路徑正確
- [ ] `container.command`: 確保包含 `source /vault/secrets/env-config && \`

**更新 kustomization.yaml**:
在 `{team}/{app}/kustomize/overlays/{env}/kustomization.yaml` 的 `patches` 區段新增:
```yaml
patches:
- path: jobs/{team}-{app}-wt.patch.yaml
  target:
    kind: WorkflowTemplate
    name: {team}-{app}-wt
```

---

#### Step 4: 建立 Base Schedule Job

**檔案位置**: `{team}/{app}/kustomize/base/jobs/{team}-{job}-sj.yaml`

**命名規則**: `{team}-{job-name}-sj.yaml`

**範本**: 見 [四、完整 YAML 範本 - Base Schedule Job](#43-base-schedule-job)

**必填 TODO 檢查清單**:

- [ ] `metadata.name`: 格式 `{team}-{job-name}-sj`（**全小寫**）
- [ ] `metadata.namespace`: 修改為你的 team name
- [ ] `metadata.annotations.batchsystem/project`: 專案名稱
- [ ] `spec.schedule`: 5 位數 cron 表達式（**最小單位是分鐘**）
- [ ] `spec.concurrencyPolicy`: 選擇 `Allow`, `Forbid`, 或 `Replace`
- [ ] `arguments.parameters.templateName`: 格式 `sit-{team}-{app}-wt`
- [ ] `arguments.parameters.jobData`: 保持 `placeholder`（避免誤執行）

**Cron Schedule 格式**:
```
格式: "分 時 日 月 週"
範例: "0 2 * * *"  # 每天凌晨 2:00 執行
範例: "*/30 * * * *"  # 每 30 分鐘執行
範例: "0 9-17 * * 1-5"  # 週一到週五 9:00-17:00 每小時執行
```

**更新 kustomization.yaml**:
在 `{team}/{app}/kustomize/base/kustomization.yaml` 的 `resources` 區段新增:
```yaml
resources:
- jobs/{team}-{job}-sj.yaml
```

---

#### Step 5: 建立 Overlay Schedule Job Patches

**檔案位置**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{job}-sj.patch.yaml`

**命名規則**: `{team}-{job-name}-sj.patch.yaml`

**範本**: 見 [四、完整 YAML 範本 - Overlay Schedule Job](#44-overlay-schedule-job)

**必填 TODO 檢查清單**:

- [ ] `metadata.labels.environment`: 修改為實際環境
- [ ] `spec.schedule`: 設定實際執行時間
- [ ] `workflowTemplateRef.name`:
  - SIT: `sit-batchsystem-main-cron-workflow-template`
  - UAT: `uat-batchsystem-main-cron-workflow-template`
  - PROD: `batchsystem-main-cron-workflow-template`（不加前綴）
  - 需要 Sharding: 加 `-sharding` 後綴
- [ ] `arguments.parameters.templateName`:
  - SIT: `sit-{team}-{app}-wt`
  - UAT: `uat-{team}-{app}-wt`
  - PROD: `{team}-{app}-wt`（不加前綴）
- [ ] `arguments.parameters.jobData`: **Base64 編碼的 JSON**

**jobData 結構**:
```json
{
  "jobName": "實際的 Java Class Name",
  "parameter": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

**編碼指令**:
```bash
# 基本編碼
echo -n '{"jobName":"MyJobClass","parameter":{"env":"sit"}}' | base64

# 複雜參數範例
echo -n '{
  "jobName": "InsuranceWriteOffJob",
  "parameter": {
    "batchSize": "1000",
    "retryCount": "3",
    "enabled": true
  }
}' | base64
```

**重要說明**:
- `jobName` 必須與 Java code 中 `getJobName()` 回傳值**完全一致**
- `parameter` 會被 deserialize 到 Java job 的參數物件中

**更新 kustomization.yaml**:
在 `{team}/{app}/kustomize/overlays/{env}/kustomization.yaml` 的 `patches` 區段新增:
```yaml
patches:
- path: jobs/{team}-{job}-sj.patch.yaml
  target:
    kind: CronWorkflow
    name: {team}-{job}-sj
```

---

#### Step 6: 驗證配置

**驗證指令**:
```bash
# 從 repo 根目錄執行
kustomize build {team}/{app}/kustomize/overlays/sit | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

**成功範例輸出**:
```
Summary: 12 resources found in 1 file - Valid: 12, Invalid: 0, Errors: 0, Skipped: 0
```

**常見錯誤處理**:
1. **metadata.name contains uppercase**: 檢查所有 name 是否全小寫
2. **invalid base64**: 檢查 jobData 是否正確編碼
3. **invalid cron expression**: 確認是 5 位數格式
4. **image not found**: 確認 image 路徑和 tag 存在

---

### 情境 B: 既有專案新增 Job（wt 已存在）

當專案已經有 WorkflowTemplate（wt）配置，只需要新增新的 Schedule Job。

**執行步驟**:
1. [Step 4: 建立 Base Schedule Job](#step-4-建立-base-schedule-job)
2. [Step 5: 建立 Overlay Schedule Job Patches](#step-5-建立-overlay-schedule-job-patches)
3. [Step 6: 驗證配置](#step-6-驗證配置)

**說明**:
- 複用既有的 WorkflowTemplate
- 每個新 job 對應一組 sj.yaml 和 sj.patch.yaml
- 不需要修改 wt 相關檔案

---

## 三、重要注意事項

### 3.1 命名限制 ⚠️

**強制規則**:
- ✅ `metadata.name` **必須全小寫**
- ✅ 使用連字號 `-` 分隔單字
- ❌ **不可使用大寫字母**
- ❌ **不可使用底線 `_`**

**正確範例**:
```yaml
metadata:
  name: rd3-jkopay-insurance-argojob-wt  ✅
  name: rd3-insurance-job-a-sj  ✅
```

**錯誤範例**:
```yaml
metadata:
  name: rd3-Jkopay-Insurance-Argojob-wt  ❌ 有大寫
  name: rd3_insurance_job_a_sj  ❌ 使用底線
```

---

### 3.2 環境前綴規則

| 環境 | WorkflowTemplate Name | Schedule Job templateName | workflowTemplateRef |
|------|----------------------|---------------------------|---------------------|
| **SIT** | `sit-{team}-{app}-wt` | `sit-{team}-{app}-wt` | `sit-batchsystem-main-cron-workflow-template` |
| **UAT** | `uat-{team}-{app}-wt` | `uat-{team}-{app}-wt` | `uat-batchsystem-main-cron-workflow-template` |
| **PROD** | `{team}-{app}-wt` | `{team}-{app}-wt` | `batchsystem-main-cron-workflow-template` |

**重要**: 環境前綴由 Kustomize 的 `namePrefix` 自動添加，但 Schedule Job 內的參數需手動指定正確的名稱。

---

### 3.3 PROD 環境最佳實踐 🔒

**建議流程**:
1. 先建立 SIT/UAT 環境的 patch 檔案
2. 完成功能開發和測試
3. **確認上 PROD 後**才建立 PROD 的 patch 檔案

**原因**:
- 避免測試中的設定被誤帶上 PROD
- 寧可缺少檔案不執行，也不要意外執行

**錯誤情境範例**:
```
Branch A: 開發 Job A，建立了所有環境的 sj.patch.yaml（包含 PROD）
Branch B: 已測試完成，準備上 PROD
結果: Branch A 的 Job A 設定被一起帶上 PROD → 意外執行 ❌
```

---

### 3.4 參數格式要求

#### jobData 必須 Base64 編碼
```bash
# ❌ 錯誤: 直接使用 JSON
value: '{"jobName":"MyJob","parameter":{}}'

# ✅ 正確: Base64 編碼
value: ewogICAiam9iTmFtZSI6Ik15Sm9iIiwKICAgInBhcmFtZXRlciI6e30KfQ==
```

#### schedule 必須是 5 位數
```yaml
# ✅ 正確: 5 位數 (分 時 日 月 週)
schedule: "0 2 * * *"
schedule: "*/30 * * * *"

# ❌ 錯誤: 6 位數 (包含秒)
schedule: "0 0 2 * * *"
```

#### jobName 必須與 Java code 一致
```java
// Java code
public class InsuranceWriteOffJob implements Job {
    @Override
    public String getJobName() {
        return "InsuranceWriteOffJob";  // 必須與 jobData 中的 jobName 一致
    }
}
```

```yaml
# YAML jobData (decoded)
{
  "jobName": "InsuranceWriteOffJob",  # 必須完全相符
  "parameter": {}
}
```

---

### 3.5 Vault 配置

所有環境都使用 **Vault Sidecar** 注入環境變數：

```yaml
# 使用 Vault Sidecar
spec:
  templates:
    - name: main
      metadata:
        annotations:
          vault.hashicorp.com/agent-inject: "true"
          vault.hashicorp.com/agent-pre-populate-only: "true"
          vault.hashicorp.com/role: "{team}-batchsystem"
          vault.hashicorp.com/agent-inject-secret-env-config: "secret/data/{env}/{team}/app/{app}"
          vault.hashicorp.com/agent-inject-template-env-config: |
            {{- with secret "secret/data/{env}/{team}/app/{app}" -}}
            {{- range $k, $v := .Data.data }}
            export {{ $k }}='{{ $v }}'
            {{- end }}
            exec "$@"
            {{- end }}
      container:
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            java -jar /app.jar ...
```

**Vault 路徑格式**: `secret/data/{env}/{team}/app/{app}`
- SIT: `secret/data/sit/rd3/app/jkopay-insurance`
- UAT: `secret/data/uat/rd3/app/jkopay-insurance`
- PROD: `secret/data/prod/rd3/app/jkopay-insurance`

**Vault Role 申請**:
- 格式: `{team}-batchsystem`
- 需找 **SRE 團隊**申請
- 每個 team 只需申請一次

---

### 3.6 concurrencyPolicy 選項

| Policy | 行為 | 使用時機 |
|--------|------|----------|
| **Allow** | 允許並行執行 | Job 執行時間短，且允許同時執行多個實例 |
| **Forbid** | 禁止並行，跳過新的執行 | Job 執行時間可能超過 schedule 間隔，且不應重複執行 |
| **Replace** | 停止舊的，執行新的 | 只需要最新的執行結果，可以犧牲舊的執行 |

**推薦**:
- 大多數情況使用 `Forbid` 避免重複執行
- 確定需要並行才使用 `Allow`

---

### 3.7 Sharding 功能

當需要分片執行（parallel processing）時:

```yaml
# Schedule Job patch
spec:
  workflowSpec:
    workflowTemplateRef:
      name: sit-batchsystem-main-cron-workflow-template-sharding  # 加 -sharding 後綴
    arguments:
      parameters:
        - name: instanceCount
          value: "5"  # 分成 5 個實例執行
```

---

## 四、完整 YAML 範本

### 4.1 Base WorkflowTemplate

**檔案**: `{team}/{app}/kustomize/base/jobs/{team}-{app}-wt.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: rd3-jkopay-insurance-argojob-wt #TODO: 通常會跟檔名一樣，請遵照格式命名 {team name}-{app-name}-wt
  namespace: rd3 #TODO: 請修改team name
  annotations:
    #TODO: 為了管理後台查詢的方便，這邊請填上專案名稱(建議用git repo上名稱)，例如：jkopay-batchsystem, jkopay-insurance
    batchsystem/project: jkopay-insurance
spec:
  serviceAccountName: rd3-batchsystem-sa #TODO: 請遵照格式命名 {team name}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1" #需要sharding時由sj填寫，這裡只是預設值，勿改
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metadata:
        annotations:
          vault.hashicorp.com/agent-inject: "true"
          #TODO: 請遵照格式命名 {team name}-batchsystem，須找SRE申請新vault role
          vault.hashicorp.com/role: "rd3-batchsystem"
          vault.hashicorp.com/agent-pre-populate-only: "true"
          vault.hashicorp.com/agent-inject-secret-env-config: "secret/data/sit/rd3/app/jkopay-insurance" #TODO: 下面的vault.hashicorp.com/agent-inject-template-env-config也要一起改
          vault.hashicorp.com/agent-inject-template-env-config: |
            {{- with secret "secret/data/sit/rd3/app/jkopay-insurance" -}}
            {{- range $k, $v := .Data.data }}
            export {{ $k }}='{{ $v }}'
            {{- end }}
            exec "$@"
            {{- end }}
      metrics:
        prometheus:
          - name: job_execute_result_counter
            labels:
              - key: team
                value: '{{workflow.namespace}}'
              - key: name
                value: '{{workflow.parameters.templateName}}'
              - key: status
                value: '{{status}}'
            help: Count of execution by result status
            counter:
              value: '1'
          - name: job_execute_duration
            help: Duration of workflow execution
            labels:
              - key: team
                value: '{{workflow.namespace}}'
              - key: name
                value: '{{workflow.parameters.templateName}}'
              - key: status
                value: '{{status}}'
            gauge:
              realtime: false
              value: '{{duration}}'
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        #TODO: 請修改為實際的 image，若不清楚可詢問SRE，或參考kustomization.yaml的images，冒號後面的tagId僅為placeholder，不須與kustomization.yaml中相同，但請務必確認image存在
        image: asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository/rd3/jkopay-insurance/sit/argojob:4c315d357931e537e189dbc1488a5ec1cf4aac11
        #TODO: 請修改為實際的 command
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            java \
              -Xmx512m -Xms512m \
              -Dspring.profiles.active=${PROFILE} \
              -Dserver.address=0.0.0.0 \
              -Dgit.commit=${GIT_COMMIT} -jar /app.jar \
              {{workflow.uid}} {{workflow.name}} \
              {{workflow.namespace}} {{inputs.parameters.jobData}} \
              {{inputs.parameters.instanceCount}} {{inputs.parameters.instanceId}}
```

---

### 4.2 Overlay WorkflowTemplate

**檔案**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{app}-wt.patch.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: rd3-jkopay-insurance-argojob-wt #TODO: 通常會跟檔名一樣，請遵照格式命名 {team name}-{app-name}-wt
  namespace: rd3 #TODO: 請修改team name
  labels:
    environment: sit #TODO: 請修改為實際的環境
spec:
  serviceAccountName: rd3-batchsystem-sa #TODO: 請遵照格式命名 {team name}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1" #需要sharding時由sj填寫，這裡只是預設值，勿改
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metadata:
        annotations:
          vault.hashicorp.com/agent-inject: "true"
          vault.hashicorp.com/agent-pre-populate-only: "true"
          #TODO: 請遵照格式命名 {team name}-batchsystem
          vault.hashicorp.com/role: "rd3-batchsystem"
          #TODO: vault.hashicorp.com/agent-inject-template-env-config也要一起改
          vault.hashicorp.com/agent-inject-secret-env-config: "secret/data/sit/rd3/app/jkopay-insurance"
          vault.hashicorp.com/agent-inject-template-env-config: |
            {{- with secret "secret/data/sit/rd3/app/jkopay-insurance" -}}
            {{- range $k, $v := .Data.data }}
            export {{ $k }}='{{ $v }}'
            {{- end }}
            exec "$@"
            {{- end }}
      metrics:
        prometheus:
          - name: job_execute_result_counter
            labels:
              - key: team
                value: '{{workflow.namespace}}'
              - key: name
                value: '{{workflow.parameters.templateName}}'
              - key: status
                value: '{{status}}'
            help: Count of execution by result status
            counter:
              value: '1'
          - name: job_execute_duration
            help: Duration of workflow execution
            labels:
              - key: team
                value: '{{workflow.namespace}}'
              - key: name
                value: '{{workflow.parameters.templateName}}'
              - key: status
                value: '{{status}}'
            gauge:
              realtime: false
              value: '{{duration}}'
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        #TODO: 請修改為實際的 image，若不清楚可詢問SRE，或參考kustomization.yaml的images
        image: asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository/rd3/jkopay-insurance/sit/argojob:4c315d357931e537e189dbc1488a5ec1cf4aac11
        #TODO: 請修改為實際的 command
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            java \
              -Xmx512m -Xms512m \
              -Dspring.profiles.active=${PROFILE} \
              -Dserver.address=0.0.0.0 \
              -Dgit.commit=${GIT_COMMIT} -jar /app.jar \
              {{workflow.uid}} {{workflow.name}} \
              {{workflow.namespace}} {{inputs.parameters.jobData}} \
              {{inputs.parameters.instanceCount}} {{inputs.parameters.instanceId}}
```

---

### 4.3 Base Schedule Job

**檔案**: `{team}/{app}/kustomize/base/jobs/{team}-{job}-sj.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  #TODO: 請符合格式規範 => {team}-{job-name}-sj
  name: rd3-job-a-sj
  namespace: rd3 #TODO: 請修改team name
  annotations:
    workflows.argoproj.io/description: |
      Shared CronWorkflow Process
    workflows.argoproj.io/version: ">= 3.2.0"
    #TODO: 為了管理後台查詢的方便，這邊請填上專案名稱(建議用git repo上名稱)，例如：jkopay-batchsystem, jkopay-insurance
    batchsystem/project: jkopay-insurance
spec:
  schedule: "0 * 1 * *" #TODO: 請修改為實際的 schedule (!!!注意!!!只有5位數，最小單位是分鐘)
  timezone: "Asia/Taipei"
  concurrencyPolicy: "Forbid" #TODO: 可用選項 {Allow, Forbid, Replace}
  workflowSpec:
    metrics:
      prometheus:
        - name: cronwf_execute_result_counter
          help: Count of execution by result status
          labels:
            - key: name
              value: '{{workflow.labels.workflows.argoproj.io/cron-workflow}}'
            - key: status
              value: '{{status}}'
            - key: workflowId
              value: '{{workflow.uid}}'
            - key: scheduledTime
              value: '{{workflow.scheduledTime}}'
          counter:
            value: '1'
        - name: cronwf_execute_duration
          help: Duration of cron workflow execution
          labels:
            - key: name
              value: '{{workflow.labels.workflows.argoproj.io/cron-workflow}}'
            - key: status
              value: '{{status}}'
          gauge:
            realtime: false
            value: '{{workflow.duration}}'
    workflowTemplateRef:
      # 重要: 不要手動添加環境前綴 (dev-, sit-)
      # 系統會自動處理環境前綴
      name: batchsystem-main-cron-workflow-template
    arguments:
      parameters:
        - name: templateName
          #TODO: 與*-wt.yaml 的 metadata.name 一致並加上環境前綴。請遵照格式命名 {env}-{team name}-{app-name}-wt
          value: sit-rd3-jkopay-insurance-argojob-wt
        - name: jobData
          #為避免還沒有要上prod，就使用base的設定誤執行，所以先使用placeholder使得就算執行，也會因為參數錯誤而跳過
          value: placeholder
```

---

### 4.4 Overlay Schedule Job

**檔案**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{job}-sj.patch.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  #TODO: 請符合格式規範 => {team}-{job-name}-sj
  name: rd3-job-a-sj
  namespace: rd3 #TODO: 請修改team name
  annotations:
    workflows.argoproj.io/description: |
      Shared CronWorkflow Process
    workflows.argoproj.io/version: ">= 3.2.0"
  labels:
    environment: sit #TODO: 請修改為實際的環境
spec:
  schedule: "0 2 * * *" #TODO: 請修改為實際的 schedule (!!!注意!!!只有5位數，最小單位是分鐘)
  timezone: "Asia/Taipei"
  workflowSpec:
    metrics:
      prometheus:
        - name: cronwf_execute_result_counter
          help: Count of execution by result status
          labels:
            - key: name
              value: '{{workflow.labels.workflows.argoproj.io/cron-workflow}}'
            - key: status
              value: '{{status}}'
            - key: workflowId
              value: '{{workflow.uid}}'
            - key: scheduledTime
              value: '{{workflow.scheduledTime}}'
          counter:
            value: '1'
        - name: cronwf_execute_duration
          help: Duration of cron workflow execution
          labels:
            - key: name
              value: '{{workflow.labels.workflows.argoproj.io/cron-workflow}}'
            - key: status
              value: '{{status}}'
          gauge:
            realtime: false
            value: '{{workflow.duration}}'
    workflowTemplateRef:
      #TODO: 手動添加環境前綴
      # SIT: sit-batchsystem-main-cron-workflow-template
      # UAT: uat-batchsystem-main-cron-workflow-template
      # PROD: batchsystem-main-cron-workflow-template (不加前綴)
      # 需要Sharding: 加 -sharding 後綴
      name: sit-batchsystem-main-cron-workflow-template
    arguments:
      parameters:
        - name: templateName
          #TODO: 與*-wt.yaml 的 metadata.name 一致並加上環境前綴
          # SIT: sit-{team}-{app}-wt
          # UAT: uat-{team}-{app}-wt
          # PROD: {team}-{app}-wt (不加前綴)
          value: sit-rd3-jkopay-insurance-argojob-wt
        - name: jobData
          # JOB 所需要的參數 請使用 base64 字串
          # Example decoded: {"jobName":"jobA","parameter":{"arg1":"1234","arg2":"3.14","arg3":[1,2,3],"arg4":true}}
          value: ewogICAicGFyYW1ldGVyIjp7CiAgICAgICJhcmcxIjoiMTIzNCIsCiAgICAgICJhcmcyIjoiMy4xNCIsCiAgICAgICJhcmczIjpbCiAgICAgICAgIDEsCiAgICAgICAgIDIsCiAgICAgICAgIDMKICAgICAgXSwKICAgICAgImFyZzQiOnRydWUKICAgfSwKICAgImpvYk5hbWUiOiJqb2JBIgp9
```

---

## 五、參考資源

### 5.1 官方文件連結

- [Argo Job YAML 設定](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1083343059/Argo+Job+yaml)
- [WorkflowTemplate 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085800917/Job+WorkflowTemplate)
- [Schedule Job 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085538635/Schedule+Job)

### 5.2 完整範例參考

**rd3/jkopay-insurance** 專案（最完整的參考實作）:

- [Base WorkflowTemplate](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/base/jobs/rd3-jkopay-insurance-argojob-wt.yaml)
- [SIT WorkflowTemplate Patch](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/overlays/sit/jobs/rd3-jkopay-insurance-argojob-wt.patch.yaml)
- [Base Schedule Job](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/base/jobs/rd3-job-a-sj.yaml)
- [SIT Schedule Job Patch](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/overlays/sit/jobs/rd3-job-a-sj.patch.yaml)
- [Base Kustomization](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/base/kustomization.yaml)
- [SIT Kustomization](https://gitlab.jkopay.app/devops/gitops/-/blob/master/rd3/jkopay-insurance/kustomize/overlays/sit/kustomization.yaml)

### 5.3 工具與驗證

**Kustomize 文件**:
- [Kustomize 官方文件](https://kubectl.docs.kubernetes.io/references/kustomize/)
- [Strategic Merge Patch](https://kubectl.docs.kubernetes.io/references/kustomize/glossary/#patchstrategicmerge)

**Kubeconform 驗證**:
- [Kubeconform GitHub](https://github.com/yannh/kubeconform)
- [CRDs Catalog](https://github.com/datreeio/CRDs-catalog)

**Argo Workflows**:
- [Argo Workflows 官方文件](https://argo-workflows.readthedocs.io/)
- [CronWorkflow Spec](https://argo-workflows.readthedocs.io/en/latest/cron-workflows/)

---

## 快速檢查清單

新增 job 時，依序確認以下項目:

### Base 檔案
- [ ] `kustomconfig.yaml` 已建立並加入 `kustomization.yaml`
- [ ] `{team}-{app}-wt.yaml` 已建立並加入 `base/kustomization.yaml` resources
- [ ] `{team}-{job}-sj.yaml` 已建立並加入 `base/kustomization.yaml` resources
- [ ] 所有 `metadata.name` 都是小寫
- [ ] Vault role 已找 SRE 申請
- [ ] Container image 路徑正確且存在

### Overlay 檔案 (每個環境)
- [ ] `{team}-{app}-wt.patch.yaml` 已建立並加入 `overlays/{env}/kustomization.yaml` patches
- [ ] `{team}-{job}-sj.patch.yaml` 已建立並加入 `overlays/{env}/kustomization.yaml` patches
- [ ] SIT 使用 `secretRef`，UAT/PROD 使用 Vault
- [ ] `workflowTemplateRef.name` 環境前綴正確
- [ ] `templateName` 環境前綴正確
- [ ] `jobData` 已 base64 編碼
- [ ] `schedule` 是 5 位數 cron 格式

### 驗證
- [ ] `kustomize build` 成功
- [ ] `kubeconform` 驗證通過
- [ ] PROD 環境在確認上線前才建立

---

## 常見問題 FAQ

### Q1: 為什麼 metadata.name 不能有大寫?
**A**: Kubernetes 資源名稱規範要求使用 DNS-1123 subdomain 格式，只允許小寫字母、數字和連字號。

### Q2: base 和 overlay 的差異是什麼?
**A**: base 定義共通配置，overlay 針對特定環境覆蓋或補充設定。類似 Spring Boot 的 `application.yaml` 和 `application-{profile}.yaml`。

### Q3: 為什麼 SIT 不使用 Vault?
**A**: SIT 環境使用 Kubernetes Secret 以簡化配置和加快部署速度。UAT/PROD 使用 Vault 以提供更嚴格的安全控管。

### Q4: jobData 解碼後是什麼格式?
**A**: 標準 JSON，包含 `jobName`（對應 Java class）和 `parameter`（傳遞給 job 的參數物件）。

### Q5: 如何確認 job 的 Java class name?
**A**: 查看 Java code 中實作 `Job` interface 的類別，其 `getJobName()` 方法的回傳值即為 `jobName`。

### Q6: concurrencyPolicy 應該選哪個?
**A**: 大多數情況選 `Forbid`（避免並行執行）。只有確定允許同時執行時才選 `Allow`。

### Q7: 如何測試 cron schedule 是否正確?
**A**: 使用線上工具如 [Crontab.guru](https://crontab.guru/)，但注意只輸入 5 位數（不含秒位）。

### Q8: 如何手動觸發 job 執行?
**A**: 在 Micro Admin 後台找到對應的 CronWorkflow，點擊手動執行按鈕。

### Q9: 為什麼驗證時出現 image not found?
**A**: 確認 image tag 確實存在於 GCR。可以執行 `gcloud artifacts docker images list` 查詢。

### Q10: 需要為每個環境建立 patch 檔案嗎?
**A**: 是的。但建議先完成 SIT/UAT 測試後，再建立 PROD 的 patch 檔案。

---

**本指南最後更新**: 2025-11-25

**維護者**: RD3 Team

**問題回報**: 請聯繫 SRE 團隊或在 GitLab issue 中提出