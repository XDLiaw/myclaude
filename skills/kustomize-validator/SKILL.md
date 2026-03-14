---
name: kustomize-validator
description: 驗證 Kustomize 配置並執行 kubeconform 檢查。當修改 YAML 配置、新增資源、或需要確認配置正確性時使用。支援自動修復常見錯誤、提供詳細報告、和環境特定驗證。
allowed-tools:
  - Bash
  - Read
  - Edit
  - Glob
---

# Kustomize Validator Skill

快速驗證 Kustomize 配置並執行 Kubernetes YAML 合規性檢查。

## 核心功能

1. **Kustomize Build 驗證** - 確認配置可以正確 build
2. **Kubeconform 檢查** - 驗證 Kubernetes 資源規範
3. **自動錯誤修復** - 修正常見的配置錯誤
4. **詳細報告** - 提供清晰的驗證結果和建議
5. **多環境驗證** - 支援同時驗證 SIT/UAT/PROD

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "驗證 Kustomize 配置"
- "檢查 YAML 是否正確"
- "測試 kustomize build"
- "執行 kubeconform"
- "確認配置無誤"
- "驗證 rd3/jkopay-insurance"

## Kustomize 檔案結構

### 標準結構

```
{team}/{app}/kustomize/
├── base/
│   ├── kustomization.yaml         # Base 資源清單
│   ├── deployment.yaml
│   ├── service.yaml
│   └── jobs/
│       ├── {team}-{app}-wt.yaml
│       └── {team}-{job}-sj.yaml
└── overlays/
    ├── sit/
    │   ├── kustomization.yaml     # SIT 覆蓋設定
    │   ├── kustomconfig.yaml      # Image 客製化
    │   └── jobs/
    │       ├── {team}-{app}-wt.patch.yaml
    │       └── {team}-{job}-sj.patch.yaml
    ├── uat/
    └── prod/
```

### kustomization.yaml 結構

```yaml
# Base kustomization.yaml
resources:
- deployment.yaml
- service.yaml
- jobs/{team}-{app}-wt.yaml
- jobs/{team}-{job}-sj.yaml

# Overlay kustomization.yaml
bases:
- ../../base

configurations:
- kustomconfig.yaml

namePrefix: sit-  # SIT/UAT only, PROD 無前綴

patches:
- path: jobs/{team}-{app}-wt.patch.yaml
  target:
    kind: WorkflowTemplate
    name: {team}-{app}-wt
```

---

## 驗證流程

### 步驟 1: 識別驗證目標

**自動識別**:
- 從使用者訊息推斷 team/app/env
- 掃描修改的檔案路徑
- 預設驗證所有環境

**手動指定**:
```
驗證 rd3/jkopay-insurance 的 SIT 環境
驗證 rd1/payment-api
驗證當前目錄
```

### 步驟 2: 執行 Kustomize Build

**指令格式**:
```bash
kustomize build {team}/{app}/kustomize/overlays/{env}
```

**檢查項目**:
- ✅ Base 資源存在
- ✅ Overlay patches 可正確套用
- ✅ 參照的檔案都存在
- ✅ YAML 語法正確
- ✅ 變數替換成功

### 步驟 3: 執行 Kubeconform 驗證

**完整指令**:
```bash
kustomize build {team}/{app}/kustomize/overlays/{env} | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

**驗證內容**:
- Kubernetes 核心資源規範
- Custom Resource Definitions (CRDs)
- Argo Workflows CRDs
- 欄位類型和必填欄位
- API 版本相容性

### 步驟 4: 分析結果

**成功範例**:
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

**失敗範例**:
```json
{
  "resources": [
    {
      "filename": "stdin",
      "kind": "WorkflowTemplate",
      "name": "rd3-Insurance-wt",
      "version": "v1alpha1",
      "status": "statusError",
      "msg": "metadata.name contains uppercase letters"
    }
  ],
  "summary": {
    "valid": 11,
    "invalid": 1,
    "errors": 0,
    "skipped": 0
  }
}
```

---

## 常見錯誤與自動修復

### 錯誤 1: 大寫字母在 metadata.name

**錯誤訊息**:
```
metadata.name contains uppercase letters
```

**原因**:
Kubernetes 資源名稱必須全小寫

**自動修復**:
1. 識別包含大寫的 name
2. 轉換為小寫
3. 更新相關引用（patches 的 target.name）
4. 重新驗證

**修復範例**:
```yaml
# 錯誤
metadata:
  name: rd3-Jkopay-Insurance-wt  # ❌

# 修正
metadata:
  name: rd3-jkopay-insurance-wt  # ✅
```

### 錯誤 2: 無效的 Base64

**錯誤訊息**:
```
invalid base64 encoding in jobData
```

**原因**:
- 包含換行符（未使用 `echo -n`）
- 特殊字元未正確編碼
- 字串被截斷

**自動修復**:
1. 解碼現有的 base64
2. 如果失敗，提示使用 jobdata-encoder Skill
3. 提供正確的編碼方式

### 錯誤 3: 無效的 Cron 表達式

**錯誤訊息**:
```
invalid cron expression in schedule
```

**原因**:
- 使用 6 位數（包含秒）
- 格式錯誤

**自動修復**:
```yaml
# 錯誤 (6 位數)
schedule: "0 0 2 * * *"  # ❌

# 修正 (5 位數)
schedule: "0 2 * * *"  # ✅
```

### 錯誤 4: 缺少資源檔案

**錯誤訊息**:
```
unable to find file: jobs/rd3-job-sj.yaml
```

**原因**:
- kustomization.yaml 引用的檔案不存在
- 檔案路徑錯誤

**自動修復**:
1. 檢查檔案是否存在於預期位置
2. 搜尋可能的正確檔案名稱
3. 更新 kustomization.yaml 或建議建立檔案

### 錯誤 5: Image 不存在

**錯誤訊息**:
```
image not found: asia-east1-docker.pkg.dev/.../tag
```

**原因**:
- Image tag 不存在於 registry
- Image 路徑錯誤

**處理方式**:
1. 提醒使用者確認 image 存在
2. 建議查看 kustomization.yaml 的 images 設定
3. 提供 gcloud 查詢指令

**查詢指令**:
```bash
gcloud artifacts docker images list \
  asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository/{team}/{app}/{env}/argojob
```

### 錯誤 6: 缺少 Patch Target

**錯誤訊息**:
```
no matches for target WorkflowTemplate/rd3-app-wt
```

**原因**:
- Base 中沒有對應的資源
- Target name 不匹配

**自動修復**:
1. 檢查 base/kustomization.yaml 是否包含該資源
2. 驗證 target.name 與 base 資源的 metadata.name 一致
3. 更新 patch 或 base 資源

---

## 驗證報告格式

### 成功報告

```markdown
## ✅ Kustomize 驗證通過

### 驗證資訊
- **專案**: rd3/jkopay-insurance
- **環境**: SIT
- **驗證時間**: 2024-01-20 14:30:00

### Kustomize Build
✅ Build 成功
- Base 資源: 8 個
- Overlay patches: 4 個
- 生成資源總數: 12 個

### Kubeconform 檢查
✅ 所有資源符合規範
- Valid: 12
- Invalid: 0
- Errors: 0
- Skipped: 0

### 資源清單
- Deployment: 2 個
- Service: 2 個
- Ingress: 1 個
- WorkflowTemplate: 1 個
- CronWorkflow: 2 個
- ServiceMonitor: 1 個
- VaultStaticSecret: 1 個

### 下一步
- ✅ 配置已驗證，可以提交
- 建議: 同時驗證 UAT/PROD 環境
```

### 失敗報告

```markdown
## ❌ Kustomize 驗證失敗

### 驗證資訊
- **專案**: rd3/jkopay-insurance
- **環境**: SIT
- **驗證時間**: 2024-01-20 14:30:00

### 錯誤摘要
- Invalid: 2 個資源
- Errors: 1 個錯誤

---

### 錯誤 #1: 大寫字母在資源名稱

**檔案**: `base/jobs/rd3-jkopay-insurance-wt.yaml`
**資源**: WorkflowTemplate/rd3-Jkopay-Insurance-wt
**錯誤**: metadata.name contains uppercase letters

**問題代碼**:
```yaml
metadata:
  name: rd3-Jkopay-Insurance-wt  # ❌ 包含大寫 J 和 I
```

**修正建議**:
```yaml
metadata:
  name: rd3-jkopay-insurance-wt  # ✅ 全小寫
```

**自動修復**:
[ ] 是否自動修復此錯誤？

---

### 錯誤 #2: 無效的 Cron 表達式

**檔案**: `base/jobs/rd3-daily-job-sj.yaml`
**資源**: CronWorkflow/rd3-daily-job-sj
**錯誤**: invalid cron expression format

**問題代碼**:
```yaml
spec:
  schedule: "0 0 2 * * *"  # ❌ 6 位數（包含秒）
```

**修正建議**:
```yaml
spec:
  schedule: "0 2 * * *"  # ✅ 5 位數（分 時 日 月 週）
```

**自動修復**:
[ ] 是否自動修復此錯誤？

---

### 錯誤 #3: 缺少資源檔案

**檔案**: `base/kustomization.yaml`
**錯誤**: unable to find file: jobs/rd3-missing-job-sj.yaml

**問題**:
kustomization.yaml 引用了不存在的檔案

**可能原因**:
1. 檔案名稱拼寫錯誤
2. 檔案尚未建立
3. 檔案路徑錯誤

**修正建議**:
1. 建立缺少的檔案
2. 從 kustomization.yaml 移除引用
3. 修正檔案路徑

---

### 修復選項

1️⃣ **自動修復所有錯誤** (推薦)
   - 修正大小寫
   - 修正 cron 格式
   - 更新引用

2️⃣ **選擇性修復**
   - 逐個確認修復

3️⃣ **僅顯示報告**
   - 手動修復

請選擇: (1/2/3)
```

---

## 多環境驗證

### 同時驗證所有環境

**指令**:
```
驗證 rd3/jkopay-insurance 所有環境
```

**處理流程**:
1. 識別所有環境（sit, uat, prod）
2. 逐個執行驗證
3. 彙總報告

**報告範例**:
```markdown
## 多環境驗證結果

### rd3/jkopay-insurance

| 環境 | Kustomize Build | Kubeconform | 有效資源 | 無效資源 | 狀態 |
|------|----------------|-------------|---------|---------|------|
| SIT  | ✅ | ✅ | 12 | 0 | ✅ 通過 |
| UAT  | ✅ | ✅ | 12 | 0 | ✅ 通過 |
| PROD | ✅ | ❌ | 11 | 1 | ❌ 失敗 |

### 詳細錯誤

#### PROD 環境
錯誤 #1: metadata.name contains uppercase
- 檔案: base/jobs/rd3-App-wt.yaml
- 建議: 將 name 改為全小寫

### 建議
- ✅ SIT 和 UAT 可以部署
- ❌ PROD 需要修復錯誤後再部署
```

---

## 自動修復功能

### 修復流程

1. **識別錯誤類型**
   - 分析 kubeconform 輸出
   - 分類錯誤（可自動修復 vs 需手動處理）

2. **生成修復計畫**
   - 列出所有可修復的錯誤
   - 預覽修復後的內容

3. **執行修復**
   - 備份原始檔案（可選）
   - 應用修復
   - 重新驗證

4. **報告結果**
   - 顯示修復的檔案
   - 顯示修復前後對比
   - 確認驗證通過

### 修復範例

```markdown
## 自動修復報告

### 修復計畫
將修復以下 2 個錯誤:

1. rd3/jkopay-insurance/base/jobs/rd3-App-wt.yaml
   - 修復: metadata.name 大小寫
   - 變更: rd3-App-wt → rd3-app-wt

2. rd3/jkopay-insurance/base/jobs/rd3-daily-sj.yaml
   - 修復: cron 表達式格式
   - 變更: "0 0 2 * * *" → "0 2 * * *"

是否執行修復？ (yes/no)

---

[使用者確認: yes]

執行修復中...

✅ 修復完成！

### 修復的檔案
1. rd3/jkopay-insurance/base/jobs/rd3-app-wt.yaml
   ```diff
   - name: rd3-App-wt
   + name: rd3-app-wt
   ```

2. rd3/jkopay-insurance/base/jobs/rd3-daily-sj.yaml
   ```diff
   - schedule: "0 0 2 * * *"
   + schedule: "0 2 * * *"
   ```

重新驗證中...

✅ 驗證通過！
- Valid: 12
- Invalid: 0

所有錯誤已修復，配置現在完全正確。
```

---

## 使用範例

### 範例 1: 快速驗證

```
User: "驗證 rd3/jkopay-insurance"

Claude: [啟用 kustomize-validator Skill]

開始驗證 rd3/jkopay-insurance...

檢查環境:
- ✅ sit/
- ✅ uat/
- ✅ prod/

驗證 SIT 環境...

執行 kustomize build...
✅ Build 成功

執行 kubeconform...
✅ 所有資源符合規範

結果:
- Valid: 12
- Invalid: 0

✅ SIT 環境驗證通過！

是否也驗證 UAT 和 PROD？ (yes/no)
```

### 範例 2: 自動修復

```
User: "檢查 YAML 是否正確，有錯就幫我修"

Claude: [啟用 kustomize-validator Skill]

開始驗證當前修改的配置...

識別到修改: rd3/jkopay-insurance/base/jobs/rd3-job-wt.yaml

執行驗證...

❌ 發現 1 個錯誤:
- metadata.name 包含大寫字母 "Job"

此錯誤可以自動修復。

執行修復...

✅ 已修復:
```yaml
metadata:
  name: rd3-job-wt  # 改為全小寫
```

重新驗證...

✅ 驗證通過！配置現在完全正確。
```

### 範例 3: 詳細報告

```
User: "詳細檢查 rd3/jkopay-insurance 的 SIT 配置"

Claude: [啟用 kustomize-validator Skill]

執行詳細驗證...

## 驗證報告: rd3/jkopay-insurance (SIT)

### Kustomize Build 分析
✅ Build 成功

**Base 資源** (8 個):
- deployment.yaml → Deployment/jkopay-insurance-api
- deployment.yaml → Deployment/jkopay-insurance-batch
- service.yaml → Service/jkopay-insurance-api
- service.yaml → Service/jkopay-insurance-batch
- ingress.yaml → Ingress/jkopay-insurance
- jobs/rd3-jkopay-insurance-wt.yaml → WorkflowTemplate
- jobs/rd3-job-a-sj.yaml → CronWorkflow
- jobs/rd3-job-b-sj.yaml → CronWorkflow

**Overlay Patches** (4 個):
- deployment.api.patch.yaml → Deployment/sit-jkopay-insurance-api
- deployment.batch.patch.yaml → Deployment/sit-jkopay-insurance-batch
- jobs/rd3-jkopay-insurance-wt.patch.yaml → WorkflowTemplate
- jobs/rd3-job-a-sj.patch.yaml → CronWorkflow

**生成資源** (12 個):
- 2 Deployments (with sit- prefix)
- 2 Services (with sit- prefix)
- 1 Ingress
- 1 ServiceMonitor
- 1 VaultStaticSecret
- 1 WorkflowTemplate
- 2 CronWorkflows

### Kubeconform 檢查
✅ 所有資源符合 Kubernetes 1.29.1 規範

**驗證內容**:
- ✅ Required fields present
- ✅ Field types correct
- ✅ API versions compatible
- ✅ CRDs validated (Argo Workflows, Vault)

### 配置健康度
**評分**: 100/100

**檢查項目**:
- ✅ 命名規則正確（全小寫）
- ✅ 環境前綴正確（sit-）
- ✅ Image 路徑格式正確
- ✅ Cron 表達式有效
- ✅ Base64 編碼正確
- ✅ 資源引用完整

### 建議
- ✅ 配置完全正確，可以安全部署
- 💡 建議: 同時驗證 UAT 環境確保一致性
```

---

## 快速參考

### 驗證指令

```bash
# 基本驗證
kustomize build {team}/{app}/kustomize/overlays/{env}

# 完整驗證
kustomize build {team}/{app}/kustomize/overlays/{env} | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

### 常見錯誤速查

| 錯誤 | 原因 | 快速修復 |
|------|------|---------|
| `uppercase in metadata.name` | 名稱包含大寫 | 改為全小寫 |
| `invalid base64` | jobData 編碼錯誤 | 使用 `echo -n` 重新編碼 |
| `invalid cron` | Cron 格式錯誤 | 使用 5 位數格式 |
| `file not found` | 引用檔案不存在 | 建立檔案或移除引用 |
| `no matches for target` | Patch target 不存在 | 檢查 base resources |

---

## 最佳實踐

### 1. 每次修改後驗證

```markdown
修改 YAML → 儲存 → 立即驗證 → 修復錯誤 → 重新驗證
```

### 2. Commit 前驗證所有環境

```markdown
修改完成 → 驗證 SIT/UAT/PROD → 全部通過 → Git commit
```

### 3. 使用 CI/CD 自動驗證

```yaml
# .gitlab-ci.yml
validate:
  script:
    - kustomize build */*/kustomize/overlays/sit | kubeconform ...
```

### 4. 定期健康檢查

```markdown
每週執行: 驗證所有專案的所有環境
確保配置持續符合最新規範
```

---

## 總結

此 Skill 提供：
- ✅ 快速 Kustomize + Kubeconform 驗證
- ✅ 自動識別常見錯誤
- ✅ 一鍵自動修復
- ✅ 詳細的錯誤說明和建議
- ✅ 多環境批次驗證
- ✅ 配置健康度評分
- ✅ 清晰的視覺化報告

讓團隊成員在修改配置時，立即獲得反饋，避免 CI/CD 失敗或部署問題。
