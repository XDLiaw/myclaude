---
name: batchsystem-gitops-scaffold
description: Use when generating GitOps YAML for BatchSystem CronWorkflows, WorkflowTemplates, Kustomize configurations, and environment overlay patches. Typically invoked as Step 3 after batchsystem-job-scaffold.
---

# batchsystem-gitops-scaffold

## 1. Input

讀取工作目錄下的 `.batchsystem-job-config.json`。

若檔案不存在，停止並提示：
```
找不到 .batchsystem-job-config.json。
請先執行 /batchsystem-schedule-job 完成需求收集，再執行此 skill。
```

重要欄位說明：

| 欄位 | 說明 |
|------|------|
| `mode` | `create` / `add` / `modify` |
| `team` | team namespace（小寫） |
| `project` | 專案名稱 |
| `jobName` | job 識別名稱（用於 CronWorkflow name） |
| `jobDescription` | CronWorkflow annotation 說明 |
| `techStack` | `dotnet` 或 `java` |
| `schedule` | 預設 cron 排程（各環境可覆寫） |
| `environments` | 陣列，元素為 `sit` / `uat` / `prod` |
| `concurrencyPolicy` | `Allow` / `Forbid` / `Replace` |
| `sharding` | `true` 啟用 sharding 模式 |
| `imageRegistry` | Docker image registry host |
| `gitopsRepo` | GitOps repo 根目錄絕對路徑 |
| `resources` | （選填）`requests`/`limits` 物件 |
| `envSchedules` | （選填）各環境自訂 schedule，key 為 `sit`/`uat`/`prod` |
| `envJobData` | 各環境 job data（物件），需 base64 encode |
| `dotnetProjectName` | .NET 專案名稱（如 `JKOPay.Insurance.Job`），由 Step 2 寫入；用於 WorkflowTemplate 的 ENTRYPOINT DLL 名稱 |

---

## 2. 變數慣例

YAML 範本中：
- `{variable}` — 本 skill 替換的變數（寫入檔案時替換掉）
- `{{workflow.xxx}}` — Argo Workflow 執行時期變數（寫入檔案時**保持雙大括號原樣**）
- Go template `{{- with ... }}` — Vault annotation 用（**保持原樣**）

環境前綴規則：

| 環境 | namePrefix | envPrefix（用於 WorkflowTemplate ref） |
|------|-----------|--------------------------------------|
| SIT  | `sit-`    | `sit-` |
| UAT  | `uat-`    | `uat-` |
| PROD | 無        | 無     |

**環境前綴規則詳解：**

| 環境 | namePrefix | workflowTemplateRef | templateName | secretRef | image path |
|------|-----------|-------------------|-------------|-----------|-----------|
| SIT | `sit-` | `sit-{team}-{project}-argojob-wt` | 同左 | `sit-{project}-secret` | `.../{env}/argojob:tag` |
| UAT | `uat-` | `uat-{team}-{project}-argojob-wt` | 同左 | `uat-{project}-secret` | `.../{env}/argojob:tag` |
| PROD | 無 | `{team}-{project}-argojob-wt` | 同左 | Vault（非 secretRef） | `.../{env}/argojob:tag` |

**PROD 特殊處理：**
- 無 `namePrefix`（kustomization.yaml 中不加 `namePrefix: prod-`）
- 使用 Vault Agent Injector 取代 `envFrom.secretRef`
- 需要額外的 WorkflowTemplate Vault patch

Shared template 名稱：
- 一般：`batchsystem-main-cron-workflow-template`
- Sharding：`batchsystem-main-cron-workflow-template-sharding`

---

## 3. 目錄結構（以 Create 模式為基準）

```
{gitopsRepo}/{team}/{project}/kustomize/
├── base/
│   ├── jobs/
│   │   ├── {team}-{project}-argojob-wt.yaml      ← WorkflowTemplate（Create 才建）
│   │   └── {team}-{jobName}-sj.yaml               ← CronWorkflow base
│   └── kustomization.yaml
└── overlays/
    ├── sit/idc/
    │   ├── jobs/
    │   │   └── {team}-{jobName}-sj.patch.yaml
    │   ├── kustomization.yaml
    │   └── kustomconfig.yaml
    ├── uat/idc/
    │   ├── jobs/
    │   │   ├── {team}-{jobName}-sj.patch.yaml
    │   │   └── {team}-{project}-argojob-wt.patch.yaml  ← UAT image/secret patch（Create 才建）
    │   ├── kustomization.yaml
    │   └── kustomconfig.yaml
    └── prod/idc/
        ├── jobs/
        │   ├── {team}-{jobName}-sj.patch.yaml
        │   └── {team}-{project}-argojob-wt.patch.yaml  ← Vault patch（Create 才建）
        ├── kustomization.yaml
        └── kustomconfig.yaml
```

> ⚠️ **重要**：SIT 和 UAT 都需要各自的 WorkflowTemplate patch。
> Base WorkflowTemplate 預設使用 SIT 的 image 和 secret。
> 若 UAT 沒有 WT patch，UAT 環境會繼承 SIT 的 `secretRef`，導致使用錯誤的 secret。

只建立 `config.environments` 包含的環境。

---

## 4. 三種模式行為

### 4.1 Create 模式（全新 App）

建立完整目錄結構，產生所有檔案。

### 4.2 Add 模式（既有 App + 新 Job）

| 動作 | 目標 |
|------|------|
| 新增 | `base/jobs/{team}-{jobName}-sj.yaml` |
| 修改 | `base/kustomization.yaml`（在最後一行 `sj.yaml` resource 後插入） |
| 新增 | `overlays/{env}/idc/jobs/{team}-{jobName}-sj.patch.yaml`（每個環境） |
| 修改 | `overlays/{env}/idc/kustomization.yaml`（在 `patches:` 區塊末尾插入） |

不建立 WorkflowTemplate、Vault patch、kustomconfig.yaml（已存在）。

### 4.3 Modify 模式

| 修改目標 | 影響檔案 |
|---------|---------|
| `schedule` | `base/jobs/{team}-{jobName}-sj.yaml` + 各環境 patch |
| `envJobData` | 各環境 patch（重算 base64） |
| `concurrencyPolicy` | `base/jobs/{team}-{jobName}-sj.yaml` + 各環境 patch |
| `suspend` | `base/jobs/{team}-{jobName}-sj.yaml` |

---

## 5. YAML 範本

### 5.1 CronWorkflow Base

檔案：`base/jobs/{team}-{jobName}-sj.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: {team}-{jobName}-sj
  namespace: {team}
  annotations:
    workflows.argoproj.io/description: "{jobDescription}"
    workflows.argoproj.io/version: ">= 3.2.0"
    batchsystem/project: {project}
spec:
  schedule: "{schedule}"
  timezone: "Asia/Taipei"
  concurrencyPolicy: "{concurrencyPolicy}"
  workflowSpec:
    metrics: # 標準 Prometheus metrics 區塊（cronwf_execute_result_counter + cronwf_execute_duration）
    workflowTemplateRef:
      name: {sharedTemplateName}
    arguments:
      parameters:
        - name: templateName
          value: {workflowTemplateName}
        - name: jobData
          value: placeholder
```

**Sharding 模式**：`sharedTemplateName` 改用 `batchsystem-main-cron-workflow-template-sharding`，並在 `arguments.parameters` 末尾加：
```yaml
        - name: instanceCount
          value: "{instanceCount}"
```

### 5.2 WorkflowTemplate Base（Create 模式才建立）

檔案：`base/jobs/{team}-{project}-argojob-wt.yaml`

**dotnet 版：**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{project}-argojob-wt
  namespace: {team}
spec:
  serviceAccountName: {team}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1"
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metrics: # 標準 Prometheus metrics 區塊（job_execute_result_counter + job_execute_duration，labels: team/name/status/jobName）
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        image: {imageRegistry}/{team}/{project}/sit/argojob:latest
        envFrom:
          - secretRef:
              name: sit-{project}-secret
        command:
          - "dotnet"
          - "{DotnetProjectName}.dll"
          - "{{workflow.uid}}"
          - "{{workflow.name}}"
          - "{{workflow.namespace}}"
          - "{{inputs.parameters.jobData}}"
          - "{{inputs.parameters.instanceCount}}"
          - "{{inputs.parameters.instanceId}}"
```

**java 版**（`command` 區塊替換為）：
```yaml
        command:
          - "bash"
          - "-c"
          - |
            java -Xmx512m -Xms512m \
              -Dspring.profiles.active=${PROFILE} \
              -Dserver.address=0.0.0.0 \
              -Dgit.commit=${GIT_COMMIT} -jar /app.jar \
              {{workflow.uid}} {{workflow.name}} \
              {{workflow.namespace}} {{inputs.parameters.jobData}} \
              {{inputs.parameters.instanceCount}} {{inputs.parameters.instanceId}}
```

**Resources（若 `config.resources` 存在，加在 `container:` 下）：**
```yaml
        resources:
          requests:
            memory: "{requests.memory}"
            cpu: "{requests.cpu}"
          limits:
            memory: "{limits.memory}"
            cpu: "{limits.cpu}"
```

### 5.3 CronWorkflow Overlay Patch

檔案：`overlays/{env}/idc/jobs/{team}-{jobName}-sj.patch.yaml`

計算 jobData base64：將 `config.envJobData[env]` 物件 JSON 序列化後 base64 encode。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: {team}-{jobName}-sj
  namespace: {team}
  labels:
    environment: {env}
spec:
  schedule: "{envSchedule}"
  concurrencyPolicy: "{concurrencyPolicy}"
  workflowSpec:
    workflowTemplateRef:
      name: {envPrefix}{team}-{project}-argojob-wt
    arguments:
      parameters:
        - name: templateName
          value: {envPrefix}{team}-{project}-argojob-wt
        - name: jobData
          value: {jobDataBase64}
```

`envSchedule`：優先使用 `config.envSchedules[env]`，不存在則用 `config.schedule`。

### 5.4 UAT WorkflowTemplate Patch（Create 模式 + UAT 環境）

檔案：`overlays/uat/idc/jobs/{team}-{project}-argojob-wt.patch.yaml`

> **為什麼需要此檔案**：Base WorkflowTemplate 的 image path 和 secretRef 預設為 SIT 環境。
> UAT 必須透過此 patch 覆寫為 UAT 專屬的 image 和 secret，否則 UAT 會誤用 SIT 的 secret。

**dotnet / java 版（格式相同）：**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{project}-argojob-wt
  namespace: {team}
spec:
  templates:
    - name: main
      container:
        image: {imageRegistry}/{team}/{project}/uat/argojob:latest
        envFrom:
          - secretRef:
              name: uat-{project}-secret
```

---

### 5.5 PROD WorkflowTemplate Vault Patch（Create 模式 + PROD 環境）

檔案：`overlays/prod/idc/jobs/{team}-{project}-argojob-wt.patch.yaml`

**dotnet 版：**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{project}-argojob-wt
  namespace: {team}
spec:
  templates:
    - name: main
      metadata:
        annotations:
          vault.hashicorp.com/agent-inject: "true"
          vault.hashicorp.com/agent-pre-populate-only: "true"
          vault.hashicorp.com/role: "{team}-batchsystem"
          vault.hashicorp.com/agent-inject-secret-env-config: "secret/data/prod/{team}/app/{project}"
          vault.hashicorp.com/agent-inject-template-env-config: |
            {{- with secret "secret/data/prod/{team}/app/{project}" -}}
            {{- range $k, $v := .Data.data }}
            export {{ $k }}='{{ $v }}'
            {{- end }}
            exec "$@"
            {{- end }}
      container:
        image: {imageRegistry}/{team}/{project}/prod/argojob:latest
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            dotnet {DotnetProjectName}.dll \
              {{workflow.uid}} {{workflow.name}} \
              {{workflow.namespace}} {{inputs.parameters.jobData}} \
              {{inputs.parameters.instanceCount}} {{inputs.parameters.instanceId}}
```

**java 版**（`command` 區塊替換為）：
```yaml
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            java -Xmx512m -Xms512m \
              -Dspring.profiles.active=${PROFILE} \
              -Dserver.address=0.0.0.0 \
              -Dgit.commit=${GIT_COMMIT} -jar /app.jar \
              {{workflow.uid}} {{workflow.name}} \
              {{workflow.namespace}} {{inputs.parameters.jobData}} \
              {{inputs.parameters.instanceCount}} {{inputs.parameters.instanceId}}
```

---

## 6. Kustomize 設定

### 6.1 kustomconfig.yaml

檔案：`overlays/{env}/idc/kustomconfig.yaml`

```yaml
images:
  - path: spec/templates[]/container/image
    kind: WorkflowTemplate
```

**偵測邏輯：**
1. 檔案存在且已含 `WorkflowTemplate` → 跳過
2. 檔案存在但缺少 → 補上 `images` 區塊
3. 檔案不存在 → 建立，並輸出說明：

```
已建立 kustomconfig.yaml。
這個檔案讓 kustomize 認得 WorkflowTemplate 裡的 container image 路徑。
沒有它的話，CI/CD 做 image 替換時會跳過 WorkflowTemplate，
導致 Job 永遠跑舊版 image。
```

### 6.2 base/kustomization.yaml

**Create 模式：**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: {team}

resources:
  - jobs/{team}-{project}-argojob-wt.yaml
  - jobs/{team}-{jobName}-sj.yaml
```

**Add 模式：**
在 `resources:` 區塊找到最後一行 `- jobs/.*-sj.yaml`，在其正後方插入：
```yaml
  - jobs/{team}-{jobName}-sj.yaml
```

### 6.3 overlays/{env}/idc/kustomization.yaml

**Create 模式（SIT）：**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../../base

namePrefix: sit-

patches:
  - path: ./jobs/{team}-{jobName}-sj.patch.yaml

configurations:
  - kustomconfig.yaml
```

> SIT 不需要 WorkflowTemplate patch，因為 Base WT 預設已使用 SIT 的 image 和 secret。

**Create 模式（UAT）：**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../../base

namePrefix: uat-

patches:
  - path: ./jobs/{team}-{jobName}-sj.patch.yaml
  - path: ./jobs/{team}-{project}-argojob-wt.patch.yaml

configurations:
  - kustomconfig.yaml
```

> ⚠️ **UAT 必須包含 WorkflowTemplate patch**（見 Section 5.4）。
> Base WT 預設為 SIT image/secret；若 UAT 缺少此 patch，會繼承 SIT 的 secret，導致錯誤的憑證被注入。

**Create 模式（PROD）：**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../../base

patches:
  - path: ./jobs/{team}-{jobName}-sj.patch.yaml
  - path: ./jobs/{team}-{project}-argojob-wt.patch.yaml

configurations:
  - kustomconfig.yaml
```

**Add 模式：**
在 `patches:` 區塊末尾插入（PROD 若有 Vault patch 行，插在其前方）：
```yaml
  - path: ./jobs/{team}-{jobName}-sj.patch.yaml
```

---

## 7. 驗證與修復

### 工具存在性檢查（驗證前必做）

在執行任何驗證前，先確認所需工具是否已安裝：

```bash
which kustomize
which kubeconform
```

| 工具 | 用途 | 未安裝時的處理方式 |
|------|------|-----------------|
| `kustomize` | Step A：YAML 組合驗證（核心） | 提示安裝，**跳過 Step A/B**，改以人工檢查代替 |
| `kubeconform` | Step B：Kubernetes Schema 驗證（選用） | 提示安裝，**跳過 Step B** |

若 `kustomize` 未安裝，提示：
```
⚠️ kustomize 未安裝，無法執行 Build 驗證。

建議安裝方式：
  brew install kustomize           # macOS
  choco install kustomize          # Windows

或下載 binary：https://kubectl.docs.kubernetes.io/installation/kustomize/

跳過自動驗證，改以人工檢查：
  1. 確認 base/kustomization.yaml 中列出的所有 resources 檔案存在
  2. 確認每個環境的 patches 路徑指向實際存在的檔案
  3. 確認 metadata.name 在 base 與 patch 中一致（包含 namespace）
  4. 確認 UAT overlay 包含 argojob-wt.patch.yaml
```

### Step A：Kustomize Build 驗證

> ⚠️ **前提**：需已安裝 `kustomize`（見上方工具存在性檢查）

對每個選擇的環境執行：
```bash
kustomize build {gitopsRepo}/{team}/{project}/kustomize/overlays/{env}/idc/
```

**檢查項目：**
- ✅ Base 資源引用存在
- ✅ Overlay patches 能正確套用
- ✅ YAML 語法正確
- ✅ 變數替換成功
- ✅ UAT overlay 包含 WorkflowTemplate patch（`overlays/uat/idc/jobs/{team}-{project}-argojob-wt.patch.yaml`），確認 UAT 使用正確的 image 和 secret（非 SIT 的）

### Step B：Kubeconform 驗證（如果有安裝）

> ⚠️ **前提**：需已安裝 `kustomize` 與 `kubeconform`（選用，見上方工具存在性檢查）

```bash
kustomize build {gitopsRepo}/{team}/{project}/kustomize/overlays/{env}/idc/ | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

若 kubeconform 未安裝，提示：
```
💡 建議安裝 kubeconform 做更完整的驗證：
  brew install kubeconform          # macOS
  choco install kubeconform         # Windows
```

### Step C：常見錯誤自動修復

若驗證失敗，檢查以下常見錯誤並提供自動修復：

| 錯誤 | 原因 | 自動修復 |
|------|------|---------|
| `metadata.name contains uppercase` | 名稱含大寫字母 | 轉為全小寫，同步更新所有引用 |
| `invalid cron expression` | Cron 格式錯誤（6 位數含秒） | 移除秒位，改為 5 位數 |
| `invalid base64 in jobData` | 編碼含換行符 | 使用 `echo -n` 重新編碼 |
| `file not found` | kustomization.yaml 引用不存在的檔案 | 檢查檔名拼寫，或移除引用 |
| `no matches for target` | Patch target 與 base 不匹配 | 比對 target.name 與 base metadata.name |
| `no resource matches strategic merge patch ... [noNs]` | Patch metadata 缺少 namespace，kustomize 無法匹配 base 資源 | 在 patch 的 metadata 中補上 `namespace: {team}` |

修復流程：
1. 列出所有可修復的錯誤
2. 預覽修復內容
3. 詢問使用者：
   ```
   發現 {n} 個可修復的錯誤。

     (a) 全部自動修復（推薦）
     (b) 逐一確認
     (c) 只顯示報告，我手動修
   ```
4. 修復後重新驗證

### Step D：驗證報告

```
## 驗證報告

### {team}/{project}

| 環境 | Kustomize Build | Kubeconform | 狀態 |
|------|:-:|:-:|------|
| SIT  | ✅ | ✅ | 通過 |
| UAT  | ✅ | ✅ | 通過 |
| PROD | ✅ | ✅ | 通過 |

資源清單：
- WorkflowTemplate: 1 個
- CronWorkflow: {n} 個

配置健康度：100/100 ✅
```

---

## 8. Completion

輸出完成摘要：

```
✅ Step 3 完成！所有 GitOps 設定已建立。

已產生/修改的檔案：
  base/jobs/{team}-{project}-argojob-wt.yaml
  base/jobs/{team}-{jobName}-sj.yaml
  base/kustomization.yaml
  overlays/sit/idc/jobs/{team}-{jobName}-sj.patch.yaml
  overlays/sit/idc/kustomization.yaml
  overlays/sit/idc/kustomconfig.yaml
  overlays/uat/idc/jobs/{team}-{jobName}-sj.patch.yaml
  overlays/uat/idc/jobs/{team}-{project}-argojob-wt.patch.yaml  ← UAT image/secret patch
  overlays/uat/idc/kustomization.yaml
  overlays/uat/idc/kustomconfig.yaml
  overlays/prod/idc/jobs/{team}-{jobName}-sj.patch.yaml
  overlays/prod/idc/jobs/{team}-{project}-argojob-wt.patch.yaml  ← Vault patch
  overlays/prod/idc/kustomization.yaml
  overlays/prod/idc/kustomconfig.yaml

🔍 驗證命令：
  kubectl kustomize overlays/sit/idc/
  kubectl kustomize overlays/prod/idc/

🎉 BatchSystem Schedule Job 建立流程全部完成！
```

完成後詢問使用者是否清除 `.batchsystem-job-config.json`：
```
是否刪除 .batchsystem-job-config.json？（已不再需要）[y/N]
```
