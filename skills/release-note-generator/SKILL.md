---
name: release-note-generator
description: 根據 Git commit 和 rollback commit 自動生成 Release Note 及上版計畫文件。當使用者提供 commit hash 並要求生成 release note、版本說明、上版文件、上版計畫時使用。支援掃描 Git 變更、分析程式碼異動、自動識別 DB 異動和 API 變更，並可直接發布到 Confluence。
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

自動化根據 Git commit 資訊生成標準化的 Release Note 文件與上版計畫。

## 整體流程 Overview

```
① 讀取專案規則         → 讀 projects/{專案}.md（標題格式、版本號、Confluence 父頁 ID、設定檔列入規則）；無則詢問是否建立
② 收集 / 推導輸入       → commit（必填）；rollback 自動推導(③)；jira_ticket 未給則自動建(⑤)；選填 release_date/prd/design
③ 自動查 rollback commit → Confluence 最新一篇 release note 的 Git commit；git rev-parse 還原完整 SHA
④ Git 變更分析          → commit 範圍 + 變更檔；識別 DB / UAPI / Vault / 設定檔(僅 production)
⑤ 自動建立 JIRA 單      → 無上版單→建上版票；偵測到 DB 異動→另建 DB 異動票（皆走 jira-ticket-creator，確認後才建）
⑥ 判斷是否產生上版計畫   → 以「變更性質」為主；單純只產 Release Note，需協調(DB/Vault/多服務/高風險)才產上版計畫
⑦ 生成文件             → Release Note（+上版計畫視⑥）；body 從 H2 開始
⑧ 發布到 Confluence     → Release Note 建父頁下、上版計畫建其子頁；JIRA 單號一律 inline smartlink
⑨ 收尾關聯             → 上版單 ↔ DB 異動票 relates；回填 Release Note「上版單」
```

詳細內容拆分於 `references/`，需要時再讀取：

| 步驟 | 參考檔案 |
|------|----------|
| ④ Git 變更分析（bash 指令、偵測邏輯、特殊情況） | `references/git-analysis.md` |
| ⑦ Release Note / 上版計畫範本與各區塊說明 | `references/templates.md` |
| 完整互動範例（兩個） | `references/examples.md` |
| ⑧⑨ Confluence 發布、JIRA inline smartlink、收尾關聯 | `references/confluence-publish.md` |
| 專案特定規則（標題/版號/父頁 ID） | `projects/{專案}.md` |

## 核心功能

1. **Git 變更分析** - 掃描指定 commit 範圍內的所有變更
2. **自動識別異動類型** - 識別 DB 異動、API 變更、設定變更等
3. **Release Note 生成** - 依據 Confluence 上的 Release Note 範本生成
4. **上版計畫生成（視情況）** - 生成獨立的上版計畫文件（作為 Release Note 子頁面）。**上版範圍單純或變更很少時可省略**，詳見「[是否產生上版計畫](#是否產生上版計畫)」。
5. **Rollback 資訊整合** - 自動查詢上一版 release note 取得 rollback commit
6. **Confluence 發布** - 支援直接發布到 Confluence（Release Note，視情況含上版計畫）

## 文件架構

```
[專案 release note 父頁面]
  └── [專案名稱] vX.Y.Z {功能} Release Note (本次 Release Note)
        └── [專案名稱] vX.Y.Z {功能} 上版計畫 (子頁面，視情況產生)
```

## 使用時機

當使用者提出以下需求時，啟用此 Skill：
- "幫我產生 release note" / "生成上版文件" / "寫 release note" / "產生版本說明"
- "commit xxx 到 yyy 的變更"
- 提供 git commit hash 並要求生成文件

---

## 操作流程

### ① 讀取專案規則

**開始生成前**先確認目標專案是否有對應規則文件（`projects/{專案}.md`，見最下方「專案特定規則索引」）。

- **有** → 讀取，取得標題格式、版本號規則、Confluence 父頁 ID、設定檔列入規則。
- **沒有** → **不要硬套其他專案的規則**。先詢問使用者是否要建立一份該專案的規則文件：
  - 使用者**同意** → 蒐集必要欄位後建立 `projects/{專案}.md`，並登錄到「專案特定規則索引」表。必要欄位：
    - Confluence 發布位置：Space ID、release note 父頁面 ID（+ URL）
    - 標題格式（如 `[XX] v{X.Y.Z} {功能} Release Note`）
    - 版本號規則（一般上版 / hotfix 如何遞增）
    - 上版計畫產生傾向、設定檔變更列入規則（哪些環境列入）
  - 使用者**不建立** → 至少請使用者當次口頭提供 **Confluence 父頁 ID** 與 **標題格式**，以便本次流程繼續。

### ② 收集 / 推導輸入

**必填**
- `commit`: 目標上版的 Git commit hash（完整或簡短皆可，預設當前最新）

**自動推導（無需使用者提供）**
- `rollback_commit`: = **上一次 release note 的 Git commit**，自動從 Confluence 查詢（見 ③）。使用者若明確指定才以使用者為準。

**選填**
- `release_date`（預設 TBD）、`jira_ticket`（未給則依 ⑤ 自動建立）、`prd_link`、`design_review_link`、`team`（預設 RD3）、`service`、`pic`

### ③ 自動查詢 rollback commit

1. 用 `getConfluencePageDescendants` 查該專案 release note 父頁面（ID 見專案規則文件）的子頁清單，**注意分頁**，找出**最新一篇** release note（版本號最大 / 清單最後一篇）。
2. 用 `getConfluencePage` 讀取該頁，從「版本控制」表取出 **Git** commit。
3. 此 commit 即本次的 **rollback commit**。
4. 僅在**查無任何既有 release note**（首次上版）時，才向使用者詢問 rollback commit。

> 取得後務必用 `git rev-parse` 還原成**完整 40 碼 SHA**（commit / rollback 皆用完整，不用簡短前綴）。

### ④ Git 變更分析

掃描 `{rollback_commit}..{commit}`，識別 DB / UAPI / Vault / 設定檔(僅 production) 異動並整理開發項目。
**完整 bash 指令、偵測邏輯與特殊情況（多 commit 範圍 / merge commit / 找不到 commit）見 `references/git-analysis.md`。**

### ⑤ 自動建立 JIRA 單（上版單 / DB 異動票）

**上版單**：若使用者未提供 `jira_ticket`，**不要**留空或填「待填寫」。在發布 Release Note 前，**自動觸發 `jira-ticket-creator` skill** 以「上版票模式」建立上版 JIRA 單，建立後以 inline smartlink 填入 Release Note 的「上版單」欄位。

**DB 異動票**：若 ④ 偵測到 **DB 異動**，除上版單外**另外自動觸發 `jira-ticket-creator`** 建立獨立的 **DB 異動票**（標題 `[RD3][<領域>] DB 異動 - xxx`，描述含 production DDL）。於 Release Note「DB 異動」區塊與上版計畫「上版前準備」以 inline smartlink 引用，並與上版單建 `relates to` 關聯。

**共通原則**：
- 皆走 `jira-ticket-creator` 確認流程：先整理欄位讓使用者確認，明確說「開單」後才建立。
- 領域 Label、Parent Epic、Sprint 等依 `jira-ticket-creator` 慣例動態查詢（不可寫死）。
- 建議順序：① 先建 DB 異動票（供文件引用）→ ② 發布 Release Note / 上版計畫 → ③ 建上版單（描述放 Release Note 連結 + 版本控制）→ ④ 回填 Release Note 的「上版單」。

### ⑥ 判斷是否產生上版計畫

見下方「[是否產生上版計畫](#是否產生上版計畫)」。

### ⑦ 生成文件

生成 Release Note（body 從 H2 開始，不含 H1），視 ⑥ 決定是否另產上版計畫。
**範本與各區塊說明見 `references/templates.md`；完整互動範例見 `references/examples.md`。**

> **不產生本地 `.md` 檔。** 草稿直接在對話中呈現供使用者確認，確認後依 ⑧ 直接發布到 Confluence。Confluence 為唯一正本（本身有版本歷史），不另存本地檔以免雙份來源 drift。

### ⑧ 發布到 Confluence（選填）

Release Note 建在專案父頁下、上版計畫建在 Release Note 子頁。**所有 JIRA 單號一律 inline smartlink。**
**發布資訊、指令、inline smartlink 寫法見 `references/confluence-publish.md`。**

### ⑨ 收尾關聯

上版單 ↔ DB 異動票 建 `relates to` 關聯；回填 Release Note「上版單」欄位（inline smartlink）。詳見 `references/confluence-publish.md`。

---

## 是否產生上版計畫

**上版計畫不一定要產生**。上版範圍單純或變更很少時，只產生 Release Note 即可，避免文件過度膨脹。

### 判斷原則

**判斷單純上版以「變更性質」為主，不以檔案數為主**（即使檔案數多，若都是 log/測試/文件等性質單純的變更，仍可省略上版計畫）。

**可以省略上版計畫的情境（單純上版）：**
- 純文案/設定值微調，無程式邏輯變更
- 只有 log/監控/告警調整（新增 log、調整 log level、新增 metric、調整告警閾值等）
- 只改測試程式碼（unit test、integration test，不影響 production 邏輯）
- 只有依賴版本升級，且**無破壞性變更**（library minor/patch 升級）
- 只有文件/註解變更（README、JavaDoc、註解等非程式碼變更）
- 無 DB / API / Vault 異動
- 單一服務、無上版順序依賴、無上版前後動作
- 無已知風險、無需特別驗收計畫（直接走預設驗收：功能正常、無錯誤）

**建議產生上版計畫的情境（需要協調）：**
- 有 DB 異動（需要 DBA 配合、有資料 migration）
- 有 Vault 異動（需要事先申請）
- 多服務協同上版、有上版順序依賴
- 有上版前準備動作（防火牆、Kafka topic、權限申請等）
- 有上版後動作（流量切換、灰度分流、資料同步等）
- 風險較高、需要明確退版步驟或驗收計畫

### 決策流程

1. 完成 Git 變更分析後，根據上述判斷原則初步評估
2. **如果不確定**，向 Eric 確認：
   ```
   本次變更範圍看起來[單純/需要協調]，是否需要產生上版計畫？

   - 變更性質: （例：純 log 調整 / 功能新增 / 設定變更 等）
   - DB 異動: 有/無
   - API 變更: 有/無
   - Vault 異動: 有/無
   - 上版順序依賴: 有/無
   ```
3. 依照 Eric 的回覆決定是否產生上版計畫；若省略，Release Note 仍正常產生

---

## 安全注意事項

1. **不要在 Release Note 中包含敏感資訊**：API keys、密碼、內部 IP 位址、個人資料。
2. **檢查 commit message 是否包含敏感資訊**：如有，提醒使用者移除。
3. **DB 異動需要 DBA 審核**：Release Note 中標註「請與 DBA 確認」。

---

## 專案特定規則索引

各專案有各自的標題格式、版本號規則與 Confluence 發布位置。
**在開始生成前，請讀取對應專案的規則文件**；若該專案尚未列於下表（無規則文件），依步驟 ① 詢問使用者是否建立。

| 專案 | 服務說明 | 規則文件 |
|------|----------|----------|
| jkos-donation | 捐款服務 | `projects/jkos-donation.md` |

> 新增專案時：建立 `projects/{專案}.md`（可參考 `jkos-donation.md` 的欄位結構），並在此表加一列。
