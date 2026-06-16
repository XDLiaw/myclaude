# Release Note / 上版計畫 範本

對應主流程 **⑦ 生成文件**。所有 body 內容**不要包含 H1 標題**（Confluence 頁面標題已是標題），直接從 H2 開始。

## 目錄
- [Release Note 範本](#release-note-範本)
- [Release Note 各區塊說明](#release-note-各區塊說明)
- [上版計畫範本](#上版計畫範本)
- [上版計畫各區塊說明](#上版計畫各區塊說明)
- [輸出方式](#輸出方式)
- [生成完成檢查清單](#生成完成檢查清單)

完整範例見 `references/examples.md`。

---

## Release Note 範本

```markdown
## 基本資訊

| 項目 | 內容 |
|------|------|
| 預計上版日期 | {release_date} |
| 上版單 | {jira_ticket} |
| PRD | [{prd_title}]({prd_link}) |
| Design Review | [{design_title}]({design_review_link}) |

## 版本控制

| 項目 | Commit |
|------|--------|
| Git | {commit_hash} |
| Rollback Git | {rollback_commit} |

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

**注意**：
- 版本控制只需 commit hash，不需 branch 名稱；commit / rollback 皆用**完整 40 碼 SHA**。
- 「上版單」與所有 JIRA 單號用 inline smartlink，發布細節見 `references/confluence-publish.md`。

## Release Note 各區塊說明

### DB 異動
如果沒有 DB 異動，填寫 `無`。如果有異動，列出（並以 inline smartlink 引用 DB 異動票）：
```markdown
- [ ] 新增 table: `table_name`
- [ ] 修改 column: `table_name.column_name`
- [ ] 新增 index: `index_name` on `table_name`
```

### UAPI 新增 routing
如果沒有新增 API，填寫 `無`。如果有新增，列出：
```markdown
- [ ] `POST /api/v1/xxx/yyy`
- [ ] `GET /api/v1/xxx/{id}`
```

### Vault 異動
如果沒有 Vault 異動，填寫 `無`。如果有異動，直接列出新增的 key 名稱（不需要額外說明）：
```markdown
- `key_name_1`
- `key_name_2`
```

### 開發項目
從 commit messages 和變更分析中整理：
```markdown
1. 功能描述 1
   - 相關檔案: `path/to/file.java`
2. 功能描述 2
   - 相關檔案: `path/to/another.java`
```

---

## 上版計畫範本

上版計畫是 Release Note 的子頁面，用於記錄上版前後的詳細執行計畫。是否產生見主流程 **⑥**。

範本來源：[上版計畫（Release Plan）範本](https://jkopay.atlassian.net/wiki/spaces/Engineering/pages/68845614/Release+Plan)

```markdown
## 上版前準備

確認上版前的相關配置(防火牆、設定檔、資料庫資料、權限、Kafka、GW…等)皆已備妥。

| Team / PIC | Description | Note / Ticket |
|------------|-------------|---------------|
| {team} / {pic} | {description} | {note} |

## 上版計畫

各個服務的上版順序依賴、上版時間、負責人、及上版內容。

| Order | Team / PIC | Service | Release Date | Note / Ticket |
|-------|------------|---------|--------------|---------------|
| 1 | {team} / {pic} | {service} | {date} | {note} |

## 上版後計畫

上版後需要接著執行的動作。例如服務的切換、資料的更新、灰度分流等。

| Team / PIC | Description | Note / Ticket |
|------------|-------------|---------------|
| {team} / {pic} | {description} | {note} |

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

## 上版計畫各區塊說明

### 上版前準備
列出上版前需要確認的所有準備事項：
- **防火牆**: 對內/對外防火牆白名單
- **設定檔**: application.yml 配置變更
- **資料庫**: DB schema 異動、資料 migration
- **權限**: 服務帳號、存取權限
- **Kafka**: Topic 建立、Consumer Group 設定
- **GW (API Gateway)**: Routing 設定

### 上版計畫
記錄各服務的上版順序：
- **Order**: 上版順序（有依賴關係時特別重要）
- **Team / PIC**: 負責團隊與負責人（合併為一欄）
- **Service**: 服務名稱
- **Release Date**: 預計上版日期時間

### 上版後計畫
上版完成後需要執行的動作：服務流量切換、資料同步/更新、灰度分流調整、監控告警設定。

### 品質控管
品質狀態標籤：`N/A`（不適用/灰色）、`PASS`（測試通過/綠色）、`SCORE`（有評分結果/藍色）、`FAIL`（測試失敗/紅色）。

### 風險控管
風險狀態標籤：`N/A`（無風險評估/灰色）、`NONE`（無已知風險/綠色）。

### 退版計畫
必須包含：
1. Rollback commit hash
2. 退版執行步驟
3. 通知清單
4. 資料回復方式（如有 DB 異動）

---

## 輸出方式

**直接生成到 Confluence，不產生本地 `.md` 檔。** 流程為：在對話中以 markdown 呈現草稿供使用者確認 → 確認後依 `references/confluence-publish.md` 直接發布到 Confluence。Confluence 為唯一正本（有版本歷史），不另存本地檔以免雙份來源 drift。

> 若使用者另有需求（例如想貼到 JIRA 或他處），可在對話中直接提供 markdown / 純文字內容，但仍不寫入本地檔。

---

## 生成完成檢查清單

生成完成後，提供檢查清單：

```markdown
## 生成完成檢查清單

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
