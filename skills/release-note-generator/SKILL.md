---
name: release-note-generator
description: 根據 Git commit 和 rollback commit 自動生成 Release Note 及上板計畫文件。當使用者提供 commit hash 並要求生成 release note、版本說明、上版文件、上板計畫時使用。支援掃描 Git 變更、分析程式碼異動、自動識別 DB 異動和 API 變更，並可直接發布到 Confluence。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - mcp__atlassian__createConfluencePage
  - mcp__atlassian__updateConfluencePage
  - mcp__atlassian__getConfluencePage
  - mcp__atlassian__getAccessibleAtlassianResources
  - mcp__atlassian__searchConfluenceUsingCql
---

# Release Note Generator Skill

自動化根據 Git commit 資訊生成標準化的 Release Note 文件與上板計畫。

## 核心功能

1. **Git 變更分析** - 掃描指定 commit 範圍內的所有變更
2. **自動識別異動類型** - 識別 DB 異動、API 變更、設定變更等
3. **Release Note 生成** - 依據 Confluence 上的 Release Note 範本生成
4. **上板計畫生成** - 生成獨立的上板計畫文件（作為 Release Note 子頁面）
5. **Rollback 資訊整合** - 自動記錄 rollback commit 資訊
6. **Confluence 發布** - 支援直接發布到 Confluence（Release Note + 上板計畫）

## 文件架構

```
[IPJ] Release Note (父頁面)
  └── [專案名稱] YYYY/MM/DD Release Note (本次 Release Note)
        └── [專案名稱] YYYY/MM/DD 上板計畫 (子頁面)
```

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "幫我產生 release note"
- "生成上版文件"
- "寫 release note"
- "產生版本說明"
- "commit xxx 到 yyy 的變更"
- 提供 git commit hash 並要求生成文件

## 操作流程

### 前置收集資訊

在開始生成前，**必須**收集以下資訊：

#### 必填資訊
- **commit**: 目標上版的 Git commit hash（完整或簡短皆可）
- **rollback_commit**: 用於退版的 Git commit hash（通常是 commit 的前一個 commit）

#### 選填資訊
- **release_date**: 預計上版日期（預設: TBD）
- **jira_ticket**: 關聯的 Jira 單號（如: INS-123）
- **prd_link**: PRD 文件連結
- **design_review_link**: Design Review 文件連結

### 資訊確認範例對話

```
Claude: 我將協助您生成 Release Note。請提供以下資訊：

1. 目標上版的 Git commit hash:
2. Rollback commit hash (退版用):

[選填]
3. 預計上版日期 (如: 2024-01-15):
4. Jira 單號 (如: INS-123):
5. PRD 連結:
6. Design Review 連結:
```

---

## Git 變更分析步驟

### Step 1: 獲取 Commit 資訊

```bash
# 獲取 commit 的完整資訊
git show {commit} --stat --format="%H%n%s%n%b"

# 獲取 branch 名稱（如果在 branch 上）
git branch --contains {commit}
```

### Step 2: 分析變更檔案

```bash
# 列出所有變更的檔案
git diff {rollback_commit}..{commit} --name-only

# 獲取詳細的變更內容
git diff {rollback_commit}..{commit} --stat

# 查看特定類型的檔案變更
git diff {rollback_commit}..{commit} --name-only -- "*.sql"
git diff {rollback_commit}..{commit} --name-only -- "*.java"
git diff {rollback_commit}..{commit} --name-only -- "*.yml" "*.yaml"
```

### Step 3: 識別異動類型

根據變更檔案自動識別以下異動類型：

#### DB 異動
檢查以下路徑/檔案的變更：
- `**/migration/**/*.sql`
- `**/db/**/*.sql`
- `**/flyway/**/*.sql`
- `**/liquibase/**`
- MyBatis mapper 中的 DDL 語句

**分析內容**：
```bash
# 檢查 SQL 檔案變更
git diff {rollback_commit}..{commit} -- "*.sql"

# 檢查是否有 CREATE TABLE, ALTER TABLE, DROP TABLE 等
git diff {rollback_commit}..{commit} | grep -E "(CREATE|ALTER|DROP|ADD|MODIFY)\s+(TABLE|COLUMN|INDEX)"
```

#### API 變更（UAPI routing）
檢查以下內容的變更：
- Controller 類別中的 `@RequestMapping`, `@GetMapping`, `@PostMapping` 等
- API 路由配置檔案
- OpenAPI/Swagger 定義

**分析內容**：
```bash
# 檢查 Controller 變更
git diff {rollback_commit}..{commit} -- "*Controller.java"

# 搜尋新增的 API endpoint
git diff {rollback_commit}..{commit} | grep -E "@(Get|Post|Put|Delete|Patch|Request)Mapping"
```

#### Vault 異動
檢查以下內容的變更：
- `application*.yml` 中的 vault 相關配置
- `bootstrap*.yml` 中的 vault 設定
- 新增的 `@Value` 注入（可能需要 vault 配置）

**重要**: 在 `application*.yml` 中，使用 `${XXXX}` 格式的變數表示需要透過 Vault 注入。
例如 `${core_backupftp_password}` 表示需要在 Vault 中設定 `core_backupftp_password` 這個 key。

**檢測方式**：
```bash
# 搜尋新增的 ${...} 格式變數
git diff {rollback_commit}..{commit} -- "*.yml" "*.yaml" | grep -E "\+.*\$\{.*\}"
```

找到的變數都需要列在 Vault 異動區塊中。

#### 設定檔變更
- `application*.yml`
- `application*.properties`
- `bootstrap*.yml`

### Step 4: 分析開發項目

根據 commit message 和變更內容，整理開發項目清單：

```bash
# 獲取 commit 範圍內的所有 commit messages
git log {rollback_commit}..{commit} --oneline

# 獲取詳細的 commit 資訊
git log {rollback_commit}..{commit} --format="%h - %s"
```

---

## Release Note 範本

### 標準格式

```markdown
# [專案名稱] vX.X.X Release Note

## 基本資訊

| 項目 | 內容 |
|------|------|
| 預計上版日期 | {release_date} |
| 上版單 | [{jira_ticket}]({jira_link}) |
| PRD | [{prd_title}]({prd_link}) |
| Design Review | [{design_title}]({design_review_link}) |

## 版本控制

| 項目 | Commit |
|------|--------|
| Git | {commit_hash} |
| Rollback Git | {rollback_commit} |

**注意**: 不需要顯示 branch 名稱，只需要 commit hash。

## 異動項目

### DB 異動
{db_changes}

### UAPI 新增 routing
{api_changes}

### Vault 異動
{vault_changes}

### 設定檔變更
{config_changes}

## 開發項目

{development_items}

## 其他備註

{other_notes}
```

### 各區塊說明

#### DB 異動
如果沒有 DB 異動，填寫 `無`

如果有異動，列出：
```markdown
- [ ] 新增 table: `table_name`
- [ ] 修改 column: `table_name.column_name`
- [ ] 新增 index: `index_name` on `table_name`
```

#### UAPI 新增 routing
如果沒有新增 API，填寫 `無`

如果有新增，列出：
```markdown
- [ ] `POST /api/v1/xxx/yyy`
- [ ] `GET /api/v1/xxx/{id}`
```

#### Vault 異動
如果沒有 Vault 異動，填寫 `無`

如果有異動，直接列出新增的 key 名稱（不需要額外說明）：
```markdown
- `key_name_1`
- `key_name_2`
```

#### 開發項目
從 commit messages 和變更分析中整理：
```markdown
1. 功能描述 1
   - 相關檔案: `path/to/file.java`
2. 功能描述 2
   - 相關檔案: `path/to/another.java`
```

---

## 自動化分析邏輯

### 1. DB 異動檢測

```python
# 偽代碼
def detect_db_changes(diff_files):
    db_changes = []

    # 檢查 SQL migration 檔案
    sql_files = [f for f in diff_files if f.endswith('.sql')]
    for sql_file in sql_files:
        content = get_file_diff(sql_file)
        if 'CREATE TABLE' in content:
            db_changes.append(f"新增 table: {extract_table_name(content)}")
        if 'ALTER TABLE' in content:
            db_changes.append(f"修改 table: {extract_table_name(content)}")

    # 檢查 MyBatis mapper
    mapper_files = [f for f in diff_files if 'mapper' in f.lower() and f.endswith('.xml')]
    # ...

    return db_changes if db_changes else ["無"]
```

### 2. API 變更檢測

```python
# 偽代碼
def detect_api_changes(diff_files):
    api_changes = []

    # 檢查 Controller 檔案
    controller_files = [f for f in diff_files if 'Controller' in f]
    for ctrl_file in controller_files:
        diff_content = get_file_diff(ctrl_file)
        # 解析新增的 @XXXMapping 註解
        mappings = extract_request_mappings(diff_content)
        api_changes.extend(mappings)

    return api_changes if api_changes else ["無"]
```

### 3. 開發項目整理

```python
# 偽代碼
def summarize_development_items(commits, diff_files):
    items = []

    # 從 commit messages 提取功能描述
    for commit in commits:
        message = commit.message
        # 移除 prefix (feat:, fix:, etc.)
        clean_message = remove_commit_prefix(message)
        items.append({
            'description': clean_message,
            'files': get_related_files(commit)
        })

    return items
```

---

## 輸出格式選項

### 選項 1: Markdown 格式（預設）
適合直接貼到 Confluence 或 Git repository

### 選項 2: Confluence Wiki 格式
適合直接在 Confluence 編輯器中使用

### 選項 3: 純文字格式
適合在 Jira 或其他系統中使用

---

## 互動式流程範例

```
User: "幫我產生 release note，commit 是 abc1234，rollback 是 def5678"

Claude (使用此 Skill):
好的，我將根據這兩個 commit 生成 Release Note。

📋 開始分析 Git 變更...

✅ 獲取 commit 資訊
   - Commit: abc1234
   - Message: feat: 新增保險訂單退款功能
   - Branch: feature/refund-feature

✅ 分析變更檔案
   - 變更檔案數: 15
   - Java 檔案: 10
   - SQL 檔案: 2
   - YAML 檔案: 3

✅ 識別異動類型
   - DB 異動: 發現 2 個 SQL migration
   - API 變更: 發現 3 個新增 endpoint
   - Vault 異動: 無
   - 設定變更: 發現 1 個設定檔變更

📄 生成 Release Note...

---

# jkopay-insurance v1.2.0 Release Note

## 基本資訊

| 項目 | 內容 |
|------|------|
| 預計上版日期 | TBD |
| 上版單 | [待填寫]() |
| PRD | [待填寫]() |
| Design Review | [待填寫]() |

## 版本控制

| 項目 | Commit |
|------|--------|
| Git | abc1234 |
| Rollback Git | def5678 |

## 異動項目

### DB 異動
- [ ] 新增 table: `insurance_order_refund`
- [ ] 新增 column: `insurance_order.refund_status`

### UAPI 新增 routing
- [ ] `POST /api/v1/insurance/refund`
- [ ] `GET /api/v1/insurance/refund/{refundId}`
- [ ] `POST /api/v1/insurance/refund/{refundId}/cancel`

### Vault 異動
無

### 設定檔變更
- `application.yml`: 新增 refund 相關設定

## 開發項目

1. 新增保險訂單退款功能
   - 支援全額退款和部分退款
   - 相關檔案: `RefundController.java`, `RefundService.java`

2. 退款手續費計算
   - 依據退款時間計算手續費
   - 相關檔案: `RefundFeeCalculator.java`

## 其他備註

待補充

---

需要我補充更多資訊嗎？
- 上版日期
- Jira 單號
- PRD 連結
```

---

## 特殊情況處理

### 1. 多個 commit 範圍

如果使用者提供的是一個範圍（如 v1.0.0..v1.1.0）：

```bash
# 獲取範圍內所有 commits
git log v1.0.0..v1.1.0 --oneline

# 獲取範圍內所有變更
git diff v1.0.0..v1.1.0 --stat
```

### 2. Merge commit

如果目標 commit 是 merge commit：

```bash
# 獲取 merge commit 的內容
git show {merge_commit} --stat

# 獲取被 merge 的所有 commits
git log {merge_commit}^1..{merge_commit}^2 --oneline
```

### 3. 找不到 commit

如果 commit hash 無效：
```
❌ 找不到 commit: {commit_hash}

請確認：
1. Commit hash 是否正確
2. 是否在正確的 Git repository 中
3. 是否已經 fetch 最新的 remote changes

提示：使用 `git log --oneline -20` 查看最近的 commits
```

---

## 驗證與確認

生成完成後，提供檢查清單：

```markdown
## 生成完成檢查清單

請確認以下項目：

- [ ] 上版日期是否正確
- [ ] Jira 單號是否關聯
- [ ] DB 異動是否完整（請與 DBA 確認）
- [ ] API 變更是否需要更新 API 文件
- [ ] Vault 異動是否已申請
- [ ] 開發項目描述是否準確

## 下一步

1. 補充缺少的連結（PRD、Design Review）
2. 將 Release Note 更新到 Confluence
3. 在 Jira 單上附上 Release Note 連結
```

---

## 安全注意事項

1. **不要在 Release Note 中包含敏感資訊**
   - API keys
   - 密碼
   - 內部 IP 位址
   - 個人資料

2. **檢查 commit message 是否包含敏感資訊**
   - 如果發現，提醒使用者移除

3. **DB 異動需要 DBA 審核**
   - Release Note 中標註「請與 DBA 確認」

---

## 參考資源

### Confluence 範本
- [ReleaseNote Template](https://jkopay.atlassian.net/wiki/spaces/Mobile/pages/806256819/ReleaseNote+Template) - Mobile 版本
- [上版計畫（Release Plan）範本](https://jkopay.atlassian.net/wiki/spaces/Engineering/pages/68845614/Release+Plan) - 完整版
- [RD3 - 上版計劃 Checklist](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/976093224/RD3+-+Checklist) - 檢查清單

### RD3 Release Note 格式
參考 [NC] Release Note 系列文件的標準格式：
- 預計上版日期
- 上版單（Jira Ticket 連結）
- Git（commit only，不需要 branch）
- Rollback Git（commit only，不需要 branch）
- DB 異動
- UAPI 新增 routing
- Vault 異動（檢查 `${XXXX}` 格式的變數）
- 其他

---

## 上板計畫（Release Plan）範本

上板計畫是 Release Note 的子頁面，用於記錄上版前後的詳細執行計畫。

### 範本來源
- [上版計畫（Release Plan）範本](https://jkopay.atlassian.net/wiki/spaces/Engineerin/pages/68845614/Release+Plan)

### 上板計畫標準格式

```markdown
# [專案名稱] YYYY/MM/DD 上板計畫

## 上版前準備

確認上版前的相關配置(防火牆、設定檔、資料庫資料、權限、Kafka、GW…等)皆已備妥。

| Team | Description | PIC | Done ✅ | Note / Ticket |
|------|-------------|-----|---------|---------------|
| {team} | {description} | {pic} | | {note} |

## 上版計畫

各個服務的上版順序依賴、上版時間、負責人、及上版內容。

| Order | Team | Service | PIC | Release Date | Note / Ticket |
|-------|------|---------|-----|--------------|---------------|
| 1 | {team} | {service} | {pic} | {date} | {note} |

## 上版後計畫

上版後需要接著執行的動作。例如服務的切換、資料的更新、灰度分流等。

| Team | Description | PIC | Done ✅ | Note / Ticket |
|------|-------------|-----|---------|---------------|
| {team} | {description} | {pic} | | {note} |

## 品質控管

上線服務的測試結果、品質評分、相關測試Metric、品值報告的連結。

| Service | QA PIC | Quality Result | Reference |
|---------|--------|----------------|-----------|
| {service} | {qa_pic} | {result} | {reference} |

## 風險控管

上版內容可能帶來的風險。例如：未解決的defect帶來的影響、未測試到的test case風險、資料異動的影響等等。

| Risk Management |
|-----------------|
| {risk_description} |

## 驗收計畫

如何確認上版成功。有無需要值班驗證計畫、分階段性的驗證等等驗收情況描述。
預設的驗收情境：上版功能皆正常，無錯誤產生。

| Acceptance Check |
|------------------|
| {acceptance_criteria} |

## 退版計畫

上版後遇到災難性錯誤時的執行辦法。

| Rollback Plan |
|---------------|
| 1. 使用 rollback commit: {rollback_commit} 進行退版 |
| 2. 通知相關人員 |
| 3. {additional_steps} |
```

### 上板計畫區塊說明

#### 上版前準備
列出上版前需要確認的所有準備事項：
- **防火牆**: 對內/對外防火牆白名單
- **設定檔**: application.yml 配置變更
- **資料庫**: DB schema 異動、資料 migration
- **權限**: 服務帳號、存取權限
- **Kafka**: Topic 建立、Consumer Group 設定
- **GW (API Gateway)**: Routing 設定

#### 上版計畫
記錄各服務的上版順序：
- **Order**: 上版順序（有依賴關係時特別重要）
- **Team**: 負責團隊
- **Service**: 服務名稱
- **PIC**: 負責人（Person In Charge）
- **Release Date**: 預計上版日期時間

#### 上版後計畫
上版完成後需要執行的動作：
- 服務流量切換
- 資料同步/更新
- 灰度分流調整
- 監控告警設定

#### 品質控管
品質狀態標籤：
- `N/A` - 不適用（灰色）
- `PASS` - 測試通過（綠色）
- `SCORE` - 有評分結果（藍色）
- `FAIL` - 測試失敗（紅色）

#### 風險控管
風險狀態標籤：
- `N/A` - 無風險評估（灰色）
- `NONE` - 無已知風險（綠色）

#### 退版計畫
必須包含：
1. Rollback commit hash
2. 退版執行步驟
3. 通知清單
4. 資料回復方式（如有 DB 異動）

---

## 完整操作流程

### Step 1: 收集資訊

**必填資訊：**
- `commit`: 目標上版的 Git commit hash
- `rollback_commit`: 用於退版的 Git commit hash

**選填資訊：**
- `release_date`: 預計上版日期
- `jira_ticket`: 關聯的 Jira 單號
- `prd_link`: PRD 文件連結
- `design_review_link`: Design Review 文件連結
- `team`: 負責團隊（預設: RD3）
- `service`: 服務名稱（預設: jkopay-insurance）
- `pic`: 負責人

### Step 2: Git 變更分析

```bash
# 獲取 commit 資訊
git show {commit} --stat --format="%H%n%s%n%b"

# 分析變更檔案
git diff {rollback_commit}..{commit} --name-only

# 檢查 DB 異動
git diff {rollback_commit}..{commit} -- "*.sql"

# 檢查 API 變更
git diff {rollback_commit}..{commit} -- "*Controller.java"

# 檢查 Vault 異動 (${XXXX} 格式)
git diff {rollback_commit}..{commit} -- "*.yml" "*.yaml" | grep -E "\+.*\$\{.*\}"
```

### Step 3: 生成文件

1. **生成 Release Note** - 主文件，包含版本資訊、異動項目、開發項目
2. **生成上板計畫** - 子文件，包含執行計畫、品質控管、退版計畫

### Step 4: 發布到 Confluence（選填）

如果使用者要求發布到 Confluence：

1. 取得 Confluence Cloud ID
2. 在 [IPJ] Release Note 頁面下建立 Release Note 子頁面
3. 在 Release Note 頁面下建立上板計畫子頁面

**Confluence 發布資訊：**
- Space ID: `23003199` (RD3 Space)
- 父頁面 ID: `1469874346` ([IPJ] Release Note)
- Cloud ID: `f26ec960-9a0e-4396-966b-f9f61581d599`

---

## 互動式流程範例（含上板計畫）

```
User: "幫我產生 release note 和上板計畫，commit 是 abc1234，rollback 是 def5678，預計 2025/03/01 上版"

Claude (使用此 Skill):
好的，我將根據這兩個 commit 生成 Release Note 和上板計畫。

📋 開始分析 Git 變更...

✅ 獲取 commit 資訊
   - Commit: abc1234
   - Message: feat: 新增保險訂單退款功能

✅ 分析變更檔案
   - Java 檔案: 10
   - SQL 檔案: 2
   - YAML 檔案: 3

✅ 識別異動類型
   - DB 異動: 2 個 SQL migration
   - API 變更: 3 個新增 endpoint
   - Vault 異動: 1 個新增變數
   - 設定變更: 1 個設定檔變更

📄 生成 Release Note...

---

# [IPJ] 2025/03/01 Release Note

## 基本資訊

| 項目 | 內容 |
|------|------|
| 預計上版日期 | 2025/03/01 |
| 上版單 | [待填寫]() |
| PRD | 無 |
| Design Review | 無 |

## 版本控制

| 項目 | Commit |
|------|--------|
| Git | abc1234 |
| Rollback Git | def5678 |

## 異動項目

### DB 異動
- [ ] 新增 table: `insurance_order_refund`

### UAPI 新增 routing
- [ ] `POST /ins/refund`

### Vault 異動
- `refund_api_key`

### 設定檔變更
- `application.yml`: 新增 refund 相關設定

## 開發項目

### 1. 新增保險訂單退款功能
- **內容**: 支援全額退款和部分退款
- **相關檔案**: `RefundController.java`, `RefundService.java`

---

📄 生成上板計畫...

---

# [IPJ] 2025/03/01 上板計畫

## 上版前準備

| Team | Description | PIC | Done ✅ | Note / Ticket |
|------|-------------|-----|---------|---------------|
| RD3 | DB 異動申請 | | | 新增 insurance_order_refund table |
| RD3 | Vault 設定申請 | | | refund_api_key |

## 上版計畫

| Order | Team | Service | PIC | Release Date | Note / Ticket |
|-------|------|---------|-----|--------------|---------------|
| 1 | RD3 | jkopay-insurance | | 2025/03/01 | |

## 上版後計畫

N/A

## 品質控管

| Service | QA PIC | Quality Result | Reference |
|---------|--------|----------------|-----------|
| jkopay-insurance | | | |

## 風險控管

| Risk Management |
|-----------------|
| 無已知風險 |

## 驗收計畫

| Acceptance Check |
|------------------|
| 上版功能皆正常，無錯誤產生 |

## 退版計畫

| Rollback Plan |
|---------------|
| 1. 使用 rollback commit: def5678 進行退版 |
| 2. 通知相關人員 |

---

✅ 文件生成完成！

需要我發布到 Confluence 嗎？
- Release Note 將建立在 [IPJ] Release Note 頁面下
- 上板計畫將建立在 Release Note 頁面下
```

---

## Confluence 發布指令

使用 MCP Atlassian 工具發布到 Confluence：

### 1. 取得 Cloud ID

```javascript
// 使用 mcp__atlassian__getAccessibleAtlassianResources 取得
// Cloud ID: f26ec960-9a0e-4396-966b-f9f61581d599
```

### 2. 建立 Release Note 頁面

```javascript
mcp__atlassian__createConfluencePage({
  cloudId: "f26ec960-9a0e-4396-966b-f9f61581d599",
  spaceId: "23003199",
  parentId: "1469874346",  // [IPJ] Release Note 頁面 ID
  title: "[IPJ] YYYY/MM/DD Release Note",
  body: "{release_note_content}",
  contentFormat: "markdown"
})
```

### 3. 建立上板計畫子頁面

```javascript
mcp__atlassian__createConfluencePage({
  cloudId: "f26ec960-9a0e-4396-966b-f9f61581d599",
  spaceId: "23003199",
  parentId: "{release_note_page_id}",  // 剛建立的 Release Note 頁面 ID
  title: "[IPJ] YYYY/MM/DD 上板計畫",
  body: "{release_plan_content}",
  contentFormat: "markdown"
})
```

---

## 專案特定規則索引

各專案有各自的標題格式、版本號規則與 Confluence 發布位置。
**在開始生成前，請讀取對應專案的規則文件。**

| 專案 | 服務說明 | 規則文件 |
|------|----------|----------|
| jkos-donation | 捐款服務 | `projects/jkos-donation.md` |
