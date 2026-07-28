# DB 異動單自我檢查清單（自動代填指引）

公司規定：每張 DB 異動單都要附「資料庫異動檢查清單」做自我審查。
來源：Confluence「資料庫異動檢查清單」（Engineering space，pageId `97977131`）。
做法：把清單貼成 JIRA **comment**，答案接在每題問號後面。

本 skill 的職責：**建單後自動把清單貼成一則 comment**，能從票內容推導的題目直接代填，
不確定的留 `【待填：xxx】` 佔位，第 7 項（後續檢查）一律留空（上線後才填）。

## 產生與貼上方式（用腳本產 ADF，勿手刻）

**格式規格（已與使用者確立）**：
- 問題維持一般字重；答案以「箭頭 `→` ＋ 粗體」與問題區隔。
- 已回答的核心答案：**藍色 `#0055CC`**；`【待填】`（尚未回答）：**紅色 `#AE2E24`**。
- 括號內的補充理由維持一般字重（不上色、不加粗）。
- 顏色只能靠 ADF 的 `textColor` mark，**markdown 做不到**，所以一律用 ADF 貼。

**步驟**：
1. 依「代填邏輯」把 1.x–6.x 的答案整理成一份 answers JSON（key 為題號字串，如 `"1.1"`）。
2. 跑產生器腳本取得 ADF：
   `python scripts/build_checklist_adf.py answers.json`
   （或把 JSON 從 stdin 餵進去。腳本已內建題目文字、區塊結構、顏色與第 7 項留空邏輯。）
3. 用 `mcp__claude_ai_Atlassian__addCommentToJiraIssue`（**`contentFormat: "adf"`**，`commentBody` 放腳本輸出的 JSON 字串）貼到剛建立的票。
4. 使用者已選「直接貼、留【待填】佔位」：建單成功後直接貼，不需為 comment 再逐題確認；貼完把代填結果與所有 `【待填】` 項目回報給使用者。

**answers JSON 每題可用三種形式**（詳見腳本 docstring）：
- 字串 → 單段藍色核心答案，如 `"否"`
- `{"core": "...", "tail": "...", "pending": false}` → core 上色（`pending: true` 時紅色）＋ tail 一般字重
- `{"segments": [["文字","c"], ["文字","p"], ...]}` → 自訂多段，`c`=上色 `p`=一般
- 未提供的 1.x–6.x 題 → 腳本自動填紅色 `【待填】`。

## 代填邏輯（依變更類型推理，不要寫死答案）

先判斷變更類型，答案會不同：

- **加法型 DDL**：`ADD COLUMN`、`CREATE INDEX`、加約束 —— 不刪改既有資料
- **資料型 / 破壞型 DML**：`UPDATE` 改值、`DELETE`、backfill 回填 —— 會動到既有資料

| 題 | 代填邏輯 |
|---|---|
| 1.1 為什麼要異動 | 從描述「背景」推：支援新功能 → `新功能需求（JKO-xxxxx）`；修資料 → `修正/導正 xxx 資料` |
| 1.2 為何不用系統後台 | 預設 `無對應後台`；新功能情境 `新功能，尚無後台` |
| 1.3 之前做過類似變更? | `否` |
| 1.4 系統問題 Root Cause + 改善計畫 | 新功能／需求型 → `非問題`；bug／資料導正型 → 從背景填 Root Cause，判斷不出則 `【待填：Root Cause】` |
| 1.5 之後會再跑類似 SQL? | `否` |
| 2.1 Code Review 人員 | 預設 `@RoyHung`（見下「Review 人員」） |
| 3.1 影響資料筆數 | 描述已有 row 數 → 直接填；否則 `【待填：影響筆數】`，並**另在對話中**給一句 `SELECT COUNT(*)` 讓使用者自查（見下「影響筆數查詢」） |
| 3.2 是否 Table lock | 加法型且帶 `ALGORITHM=INPLACE, LOCK=NONE`、或小量資料 → `否`；大表未走 online DDL → `可能，建議 DBA 走 INPLACE / pt-online-schema-change` |
| 3.3 效能負面影響／執行計畫 | 一般小異動 → `否` |
| 3.4 跑多久／執行時間／避開尖峰 | **只填「跑多久」**（描述有預估耗時或可由變更類型推得，如 INSTANT 加欄位 → `數秒內`）。**「預計執行時間／是否避開尖峰」不代填、不標紅、直接留空**——取決於使用者實際排程，且低流量服務未必在意，別亂猜 |
| 3.5 與活動衝突／近假日 | `否` |
| 4.1 測試環境測試過 | `是`（SIT/UAT 由開發自行處理） |
| 5.1 是否需備份／為何不需 | 加法型 → `否，新增欄位/索引不刪除既有資料`；破壞型（DELETE／大量 UPDATE） → `【待填：是否備份】` 並提醒使用者評估 |
| 5.2 Rollback Plan | 加法型 → `不需要（可 DROP COLUMN/INDEX 還原）`；描述有退版 SQL → `見描述退版 SQL`；破壞型 → `【待填：Rollback Plan】` |
| 6.1 文件記錄 | `否` |
| 7.1 / 7.2 後續檢查 | **一律留空**（上線後才填，不要代填；腳本已自動處理） |

## 影響筆數查詢（3.1）

當 3.1 無法直接從描述得知筆數時：

1. answers 內 3.1 用 `{"core": "【待填：影響筆數】", "pending": true}`（紅色）。
2. **另在對話中**（不是在票裡）提供一句對應的計數 SQL，讓使用者自己到 DB 查回填：
   `SELECT COUNT(*) FROM <table> WHERE <與異動相同的條件>;`
   條件要與實際異動的 `WHERE` 一致（例如 backfill 用 `platform_order_id IS NULL`）。
3. **這句查詢 SQL 只給使用者，絕對不要寫進票的 description，也不要寫進 comment。**
   票裡只保留「異動本身的 SQL」與清單答案；查資料用的 SQL 屬於暫時性、不入票。

## Review 人員（2.1）

- 預設帶 `@RoyHung`（歷史慣例：SQL 一律由 Roy review）。
- 目前 `lookupJiraAccountId` 若被擋、取不到 accountId，就用純文字 `@RoyHung`，並提醒使用者貼完後可在 JIRA 內手動改成真 mention；
  若能取得 accountId，可改用 ADF mention node（`{"type":"mention","attrs":{"id":"<accountId>"}}`）。
- 使用者若指定其他 reviewer，以使用者為準。

## 題目全文（供對照；實際輸出由腳本產生）

腳本 `scripts/build_checklist_adf.py` 已內建下列題目文字與結構，代填時只需提供 answers JSON：

```
1. 變更必要性
   1.1 為什麼要進行這項資料庫異動?
   1.2 為什麼沒有辦法使用系統後台進行資料庫異動?
   1.3 之前是否曾經做過類似的變更，如果曾經做過，那麼什麼時候可以開始改用系統後台進行異動?
   1.4 如果是因為系統問題造成的需求，我們是否知道系統的 Root Cause 是什麼? 以及是否有改善計畫?
   1.5 之後是否有可能需要再次執行類似的 SQL? 如果有，那解決的計畫是?
2. 程式碼審查 (Code Review):
   2.1 SQL 是否有經過 Team Member Code Review? Review 人員是?
3. 影響分析 (Impact Analysis):
   3.1 SQL 可能影響的資料筆數?
   3.2 SQL 是否有可能造成 Table lock?
   3.3 SQL 變更是否對數據庫性能有負面影響，是否有需要跑執行計畫?
   3.4 SQL 預計會跑多久? 預計執行的時間? 是否有避開尖峰時間?
   3.5 SQL 預計執行期間是否與公司/行銷預計執行的活動有衝突? 是否鄰近假日或重要節日(e.g. 雙11)
4. 測試執行 (Testing Execution):
   4.1 SQL 是否有在測試環境進行過測試?
5. 備案 (Contingency Planning):
   5.1 資料是否有需要進行備份? 如果不需要的話，為什麼不需要?
   5.2 如果執行結果不如預期，是否有 Rollback Plan?
6. 文件記錄 (Documentation):
   6.1 如果曾經做過類似的變更，是否有文件紀錄執行過程，以及清楚列出需注意的事項?
7. 後續檢查 (Post-deployment Review):    ← 一律留空
   7.1 執行完畢後，執行結果是否符合預期
   7.2 檢查是否有未預料的問題出現
```

## answers JSON 範例（加法型 ADD COLUMN，實測於 JKO-32951）

```json
{
  "1.1": {"core": "新功能需求", "tail": "（JKO-31315，order_tab 新增 jkos_account 作為與會員系統的關聯鍵）"},
  "1.2": "無對應後台",
  "1.3": "否",
  "1.4": {"core": "非問題", "tail": "（新功能需求）"},
  "1.5": "否",
  "2.1": "@RoyHung",
  "3.1": "1,679,817 筆",
  "3.2": {"core": "否", "tail": "（ADD COLUMN nullable，MySQL 8 為 INSTANT，不鎖表）"},
  "3.3": "否",
  "3.4": {"core": "數秒內", "tail": "（ADD COLUMN nullable 為 INSTANT）"},
  "3.5": "否",
  "4.1": "是",
  "5.1": {"core": "否", "tail": "，新增欄位不刪除既有資料"},
  "5.2": {"core": "不需要", "tail": "（可 DROP COLUMN 還原；欄位 nullable、舊 code 不引用，回滾相容）"},
  "6.1": "否"
}
```

> 注意 3.4：只填「數秒內」（跑多久），沒有「會避開尖峰」——執行時間/避峰不代填。
