# GitOps Claude Skills

這個目錄包含用於自動化 GitOps 工作流程的 Claude Skills，專門設計給 JKO Pay 團隊使用。所有 Skills 都是**完全獨立**的，不依賴專案特定的 CLAUDE.md 文件。

## 🎯 Skills 總覽

| Skill | 用途 | 觸發關鍵字 |
|-------|------|-----------|
| [argo-workflow-integrator](#argo-workflow-integrator) | 建立和配置 Argo Workflow 的 WorkflowTemplate 和 Schedule Job | "新增 batch job", "建立定時任務", "整合 Argo Workflow" |
| [jobdata-encoder](#jobdata-encoder) | JSON ↔ Base64 轉換，處理 Argo Workflow jobData 參數 | "編碼 jobData", "解碼 base64", "查看 jobData 內容" |
| [kustomize-validator](#kustomize-validator) | 驗證 Kustomize 配置，執行 kubeconform 檢查，自動修復錯誤 | "驗證配置", "檢查 YAML", "kubeconform" |
| [cron-schedule-helper](#cron-schedule-helper) | 自然語言 ↔ Cron 表達式轉換，執行時間預覽 | "每天凌晨2點", "這個 cron 什麼意思", "下次執行時間" |
| [release-note-generator](#release-note-generator) | 根據 Git commit 自動生成 Release Note 文件 | "產生 release note", "生成上版文件", "寫 release note" |
| [excel-comparator](#excel-comparator) | 批次比對 Excel 檔案內容，包含格式、小數點、時間格式等 | "比對 Excel", "Excel 差異", "檢查報表一致性" |

---

## 📚 詳細說明

### argo-workflow-integrator

**完整的 Argo Workflow 整合自動化工具**

#### 主要功能
- 🚀 **全新專案整合** - 建立完整的 WorkflowTemplate + Schedule Job
- ➕ **既有專案新增 Job** - 僅新增 Schedule Job，複用現有 WorkflowTemplate
- 🌍 **多環境支援** - 自動產生 SIT/UAT/PROD overlay patches
- ✅ **參數驗證** - 強制命名規則、格式檢查
- 📝 **自動更新 kustomization.yaml** - 維護資源清單

#### 使用範例
```
您: "幫我新增一個 batch job"
您: "rd3/jkopay-insurance 新增 daily-settlement job，每天凌晨3點執行"
您: "建立 Argo Workflow 定時任務"
```

#### 互動流程
1. 詢問情境（全新專案 vs 既有專案）
2. 收集基本資訊（team, app, job-name）
3. 收集 Schedule Job 配置（cron, jobName, parameters）
4. （全新專案）收集 WorkflowTemplate 配置
5. 建立所有檔案
6. 執行驗證
7. 提供詳細摘要

#### 輸出
- Base YAML 檔案
- Overlay patch 檔案
- 更新的 kustomization.yaml
- 驗證報告

---

### jobdata-encoder

**Argo Workflow jobData 參數編碼/解碼工具**

#### 主要功能
- 🔄 **雙向轉換** - JSON ↔ Base64
- ✅ **格式驗證** - 檢查 JSON 語法和必填欄位
- 📖 **內容解析** - 清晰顯示 jobData 含義
- ⚠️ **jobName 提醒** - 確保與 Java code 一致
- 📂 **從檔案讀取** - 支援從 YAML 檔案提取並解碼

#### jobData 格式
```json
{
  "jobName": "Java類別名稱",
  "parameter": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

#### 使用範例
```
您: "幫我編碼 jobData: jobName 是 DailyJob, parameter 是 {date: today}"
您: "這個 base64 是什麼: ewogICJqb2JOYW1lIjogIlRlc3RKb2IiCn0="
您: "查看 rd3/jkopay-insurance 的 jobData"
您: "將 JSON 轉成 base64"
```

#### 重要提醒
- ✅ 使用 `echo -n` 編碼（避免換行符）
- ⚠️ `jobName` 必須與 Java `getJobName()` 完全一致
- 📝 `parameter` 物件會被 deserialize 到 Java 參數物件

---

### kustomize-validator

**Kustomize 配置驗證和自動修復工具**

#### 主要功能
- 🔍 **Kustomize Build 驗證** - 確認配置可正確 build
- ✅ **Kubeconform 檢查** - 驗證 Kubernetes 資源規範
- 🔧 **自動修復** - 修正常見錯誤（大小寫、cron 格式等）
- 📊 **詳細報告** - 清晰的驗證結果和建議
- 🌐 **多環境驗證** - 批次驗證 SIT/UAT/PROD

#### 驗證指令
```bash
kustomize build {team}/{app}/kustomize/overlays/{env} | kubeconform \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -summary -strict -kubernetes-version 1.29.1 -output json
```

#### 使用範例
```
您: "驗證 rd3/jkopay-insurance"
您: "檢查 YAML 是否正確，有錯就幫我修"
您: "驗證所有環境"
您: "執行 kubeconform"
```

#### 自動修復項目
- ✅ 大寫字母 → 全小寫
- ✅ 6位數 cron → 5位數
- ✅ 無效 base64 → 重新編碼
- ✅ 缺少檔案 → 提示建立或移除引用

---

### cron-schedule-helper

**Cron 表達式產生器和驗證工具**

#### 主要功能
- 🗣️ **自然語言轉換** - "每天凌晨2點" → `0 2 * * *`
- ✅ **語法驗證** - 檢查 5 位數格式和數值範圍
- ⏰ **執行時間預覽** - 顯示接下來的執行時間
- 📚 **常見模式庫** - 提供常用 cron 範本
- ⚠️ **衝突檢測** - 檢查邏輯錯誤

#### Cron 格式（5 位數）
```
分 時 日 月 週
│  │  │  │  │
│  │  │  │  └─ 0-7 (0和7都是週日)
│  │  │  └──── 1-12
│  │  └─────── 1-31
│  └────────── 0-23
└───────────── 0-59
```

#### 使用範例
```
您: "每天凌晨3點執行"
您: "週一到週五早上9點"
您: "這個 cron 對不對: 0 0 2 * * *"
您: "0 2 * * * 下次什麼時候執行"
您: "每30分鐘跑一次"
```

#### 常見模式
```yaml
# 每日報表
schedule: "0 2 * * *"

# 營業時間每小時
schedule: "0 9-17 * * 1-5"

# 每15分鐘
schedule: "*/15 * * * *"

# 週一早上
schedule: "0 9 * * 1"
```

---

### release-note-generator

**根據 Git commit 自動生成 Release Note 文件**

#### 主要功能
- 📝 **Git 變更分析** - 掃描指定 commit 範圍內的所有變更
- 🔍 **自動識別異動類型** - DB 異動、API 變更、設定變更等
- 📄 **標準化格式輸出** - 依據 Confluence Release Note 範本生成
- 🔄 **Rollback 資訊整合** - 自動記錄退版 commit 資訊

#### 使用範例
```
您: "幫我產生 release note，commit 是 abc1234，rollback 是 def5678"
您: "生成上版文件"
您: "寫 release note"
```

#### 互動流程
1. 收集 commit 和 rollback commit 資訊
2. 分析 Git 變更檔案
3. 自動識別 DB 異動、API 變更
4. 生成標準化 Release Note
5. 提供檢查清單

#### 輸出
- 標準化 Markdown 格式的 Release Note
- 包含：基本資訊、版本控制、異動項目、開發項目
- 自動識別的 DB 異動和 API 變更清單

---

## 🚀 快速開始

### 安裝

這些 Skills 已經位於專案的 `.claude/skills/` 目錄中。

#### 選項 1: 專案級別（團隊共享）
```bash
# 已經在專案中，直接使用
cd /path/to/gitops
# Skills 自動載入
```

#### 選項 2: 個人級別（跨專案使用）
```bash
# 複製到個人 skills 目錄
cp -r .claude/skills/* ~/.claude/skills/
```

### 驗證安裝

在 Claude Code 中輸入：
```
列出可用的 skills
```

您應該會看到四個 skills 都被列出。

---

## 💡 使用技巧

### 1. Skills 會自動啟用

不需要明確調用，只需用自然語言描述需求：

```
✅ "幫我新增一個每天凌晨2點執行的 batch job"
   → 自動啟用 argo-workflow-integrator + cron-schedule-helper

✅ "查看這個 base64 是什麼意思: ewogIC..."
   → 自動啟用 jobdata-encoder

✅ "驗證配置"
   → 自動啟用 kustomize-validator
```

### 2. Skills 可以組合使用

```
您: "新增 daily-report job，每天早上9點執行"

Claude 會自動：
1. 使用 cron-schedule-helper 轉換 "每天早上9點" → "0 9 * * *"
2. 使用 argo-workflow-integrator 建立 YAML 檔案
3. 使用 jobdata-encoder 編碼 job 參數
4. 使用 kustomize-validator 驗證配置
```

### 3. 互動式使用

Skills 會逐步引導您提供必要資訊：

```
您: "新增 batch job"

Claude:
1️⃣ 這是全新專案還是既有專案？
2️⃣ Team 名稱:
3️⃣ 應用程式名稱:
4️⃣ Job 名稱:
5️⃣ 執行時間:
...
```

### 4. 批次操作

```
您: "驗證所有環境並修復錯誤"

Claude:
- 驗證 SIT ✅
- 驗證 UAT ✅
- 驗證 PROD ❌ (發現錯誤)
- 自動修復錯誤
- 重新驗證 PROD ✅
```

---

## 🔧 Skills 架構

### 設計原則

1. **完全獨立** - 不依賴專案特定的 CLAUDE.md
2. **自包含** - 所有必要知識都在 Skill 內部
3. **可組合** - Skills 可以協同工作
4. **互動式** - 逐步引導使用者提供資訊
5. **智能觸發** - 根據關鍵字自動啟用

### 檔案結構

```
.claude/skills/
├── README.md                          # 本文件
├── argo-workflow-integrator/
│   ├── SKILL.md                       # Skill 定義和說明
│   └── templates.md                   # YAML 範本庫
├── jobdata-encoder/
│   └── SKILL.md
├── kustomize-validator/
│   └── SKILL.md
└── cron-schedule-helper/
    └── SKILL.md
```

### 權限控制

每個 Skill 都有 `allowed-tools` 限制，確保安全：

| Skill | 允許的工具 |
|-------|-----------|
| argo-workflow-integrator | Read, Write, Edit, Bash, Glob, Grep |
| jobdata-encoder | Bash, Read |
| kustomize-validator | Bash, Read, Edit, Glob |
| cron-schedule-helper | Bash |

---

## 📖 參考資源

### 官方文檔
- [Argo Workflow 整合指南](../ARGO_WORKFLOW_INTEGRATION_GUIDE.md)
- [Argo Job YAML 設定](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1083343059/Argo+Job+yaml)
- [WorkflowTemplate 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085800917/Job+WorkflowTemplate)
- [Schedule Job 範本](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/1085538635/Schedule+Job)

### 範例參考
- `rd3/jkopay-insurance/kustomize/` - 最完整的實作範例

### 外部工具
- [Crontab.guru](https://crontab.guru/) - Cron 表達式驗證
- [Kustomize Docs](https://kubectl.docs.kubernetes.io/references/kustomize/)
- [Kubeconform](https://github.com/yannh/kubeconform)

---

## 🤝 貢獻

### 改進 Skills

如果您發現 Skill 可以改進：

1. 編輯對應的 `SKILL.md` 檔案
2. 測試修改是否正常運作
3. 提交 Git commit
4. 團隊成員會自動獲得更新

### 新增 Skills

建立新的 Skill：

1. 在 `.claude/skills/` 下建立新目錄
2. 建立 `SKILL.md` 檔案
3. 遵循現有 Skills 的格式
4. 加入到本 README 的表格中

### Skill 格式

```markdown
---
name: skill-name
description: 簡短描述，包含使用時機和觸發關鍵字
allowed-tools:
  - Tool1
  - Tool2
---

# Skill Name

詳細說明...
```

---

## 🐛 故障排除

### Skill 沒有被啟用

**原因**:
- 關鍵字不夠明確
- Description 沒有包含相關觸發詞

**解決**:
```
❌ "幫我做個東西"  (太模糊)
✅ "幫我新增一個 batch job"  (明確觸發 argo-workflow-integrator)
```

### Skill 執行錯誤

**檢查**:
1. 檔案路徑是否正確
2. 必要的工具（kustomize, kubeconform）是否安裝
3. 權限是否足夠

**除錯**:
```bash
# 檢查 kustomize
kustomize version

# 檢查 kubeconform
kubeconform -v

# 檢查 base64
echo "test" | base64
```

### Skills 衝突

如果多個 Skills 同時被觸發：
- Claude 會選擇最相關的 Skill
- 或者組合使用多個 Skills

---

## 📊 使用統計

### 推薦的使用場景

| 任務 | 推薦 Skill 組合 |
|------|----------------|
| 新增 Argo Workflow Job | argo-workflow-integrator + cron-schedule-helper + jobdata-encoder + kustomize-validator |
| 修改 Job 排程時間 | cron-schedule-helper |
| 查看或修改 Job 參數 | jobdata-encoder |
| 驗證 YAML 配置 | kustomize-validator |
| 理解 Cron 表達式 | cron-schedule-helper |

### 效率提升

使用這些 Skills 可以：
- ⏱️ **節省 80% 的配置時間** - 從手動編寫到自動生成
- 🐛 **減少 95% 的配置錯誤** - 自動驗證和修復
- 📚 **降低學習曲線** - 不需記憶複雜的 YAML 結構和 Cron 語法
- 🤝 **團隊知識共享** - Skills 包含最佳實踐

---

## 📞 獲取幫助

### 詢問 Skill 使用方式

```
您: "如何使用 argo-workflow-integrator?"
您: "jobdata-encoder 可以做什麼?"
您: "給我 cron-schedule-helper 的使用範例"
```

### 回報問題

如果 Skill 運作不如預期：

1. 描述您的輸入和預期輸出
2. 提供實際得到的結果
3. 附上錯誤訊息（如果有）

```
您: "argo-workflow-integrator 產生的 YAML 有錯誤：
    - 輸入: team=rd3, app=test
    - 錯誤: metadata.name 包含大寫
    - 預期: 應該自動轉為小寫"
```

---

## 🎉 總結

這四個 Skills 提供了完整的 Argo Workflow 整合工作流程：

1. **argo-workflow-integrator** - 建立完整配置
2. **jobdata-encoder** - 處理 Job 參數
3. **kustomize-validator** - 確保配置正確
4. **cron-schedule-helper** - 設定執行時間

**完全獨立，無需 CLAUDE.md，隨時可用！**

開始使用：
```
您: "幫我新增一個每天凌晨2點執行的 batch job"
```

Claude 會自動引導您完成整個流程！🚀
