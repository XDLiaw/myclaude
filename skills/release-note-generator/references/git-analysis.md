# Git 變更分析

對應主流程 **④ Git 變更分析**。掃描 `{rollback_commit}..{commit}` 範圍，識別 DB / UAPI / Vault / 設定檔等異動類型，並整理開發項目。

## 目錄
- [Step 1: 獲取 Commit 資訊](#step-1-獲取-commit-資訊)
- [Step 2: 分析變更檔案](#step-2-分析變更檔案)
- [Step 3: 識別異動類型](#step-3-識別異動類型)
- [Step 4: 分析開發項目](#step-4-分析開發項目)
- [自動化分析邏輯（偽代碼）](#自動化分析邏輯偽代碼)
- [特殊情況處理](#特殊情況處理)

---

## Step 1: 獲取 Commit 資訊

```bash
# 獲取 commit 的完整資訊
git show {commit} --stat --format="%H%n%s%n%b"

# 獲取 branch 名稱（如果在 branch 上）
git branch --contains {commit}
```

## Step 2: 分析變更檔案

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

## Step 3: 識別異動類型

根據變更檔案自動識別以下異動類型：

### DB 異動
檢查以下路徑/檔案的變更：
- `**/migration/**/*.sql`
- `**/db/**/*.sql`
- `**/flyway/**/*.sql`
- `**/liquibase/**`
- MyBatis mapper 中的 DDL 語句
- **測試 schema（如 `**/h2/schema-*.sql`）**：本專案常以 H2 測試 schema 反映 production DB 異動（例如 `schema-v3_11_0.sql`）。雖位於測試資源路徑，仍代表真實 production 欄位/表異動 → **視為 DB 異動**，並提醒提供 production DDL 給 DBA。

**分析內容**：
```bash
# 檢查 SQL 檔案變更
git diff {rollback_commit}..{commit} -- "*.sql"

# 檢查是否有 CREATE TABLE, ALTER TABLE, DROP TABLE 等
git diff {rollback_commit}..{commit} | grep -E "(CREATE|ALTER|DROP|ADD|MODIFY)\s+(TABLE|COLUMN|INDEX)"
```

> 偵測到 DB 異動時，依主流程 **⑤** 另建 DB 異動 JIRA 票（production DDL）。

### API 變更（UAPI routing）
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

> 只列**新增**的 routing；既有 endpoint 僅增加欄位不算新 routing。被移除的 route 可記在開發項目/其他備註。

### Vault 異動
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

### 設定檔變更
- `application*.yml`
- `application*.properties`
- `bootstrap*.yml`

> 只列影響 **production** 環境的設定變更；`application-dev.yml`／`application-local.yml` 等非 production 設定，以及純 build/deploy pipeline 變更（image 命名等），依專案規則判斷是否列入。

## Step 4: 分析開發項目

根據 commit message 和變更內容，整理開發項目清單：

```bash
# 獲取 commit 範圍內的所有 commit messages
git log {rollback_commit}..{commit} --oneline

# 獲取詳細的 commit 資訊
git log {rollback_commit}..{commit} --format="%h - %s"
```

---

## 自動化分析邏輯（偽代碼）

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
