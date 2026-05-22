---
name: self-mock-management
description: Use when the user wants to create, modify, search, or remove mock scenarios on the Self-Mock-Server platform — e.g., simulating payment success/failure, billing query, refund flows for third-party services (中華電信 EFCS、台新 NPI、凱擘 CNS、關貿、遠通 etc.). Triggers on requests like 「幫我模擬中華電信查繳失敗」、「加一個台新 EFCS 退款 scenario」、「找看看有沒有現成的 cht 繳費成功情境」。
---

# Self-Mock-Server 操作流程（Session 1）

協助 PM / RD / SDET 用自然語言描述需求，透過 MCP tools 在測試環境的 Self-Mock-Server 上建立、修改、查詢 mock scenario。**不需要手寫 JSON、不需要懂底層 config 結構**。

---

## 本 skill 不涵蓋（請轉路由）

| 你想做的事 | 用哪個 skill / 工具 |
|---|---|
| 把測試環境的 scenario 改動帶回本機 repo / 發 MR | `self-mock-apply-change-record` |
| 從一個現成 scenario 拷貝改幾個欄位 | `self-mock-clone` |
| 依 reference「常見測試情境」表批次建一組 scenario | `self-mock-bulk-scenarios` |
| 從真實 request/response trace（curl、HAR、log）反推 scenario | `self-mock-from-trace` |
| 診斷「為什麼這個 request 沒打到我以為的 scenario」 | `self-mock-trace` |
| 審 scenario 重疊條件、孤兒、命名違規 | `self-mock-lint` |
| 比較不同來源（SIT MCP / 本機 clone）的 scenario 差異 | `self-mock-diff-envs` |
| 匯出 / 還原整個平台 scenario | `self-mock-snapshot` |
| 盤點 scenario vs 測試碼引用 | `self-mock-coverage` |
| 新增 service 的知識庫（reference）文件 | `self-mock-reference-gen` |

本 skill 專注於 **平台上單一 scenario 的 CRUD 操作**。其他 skill 都是它的延伸。

---

## 語言規則

所有輸出使用**繁體中文**。技術術語（API 路徑、欄位名、scenario 名、MCP tool 名）保留英文原文。

---

## 適用對象

- **PM**：收到客訴想復現問題、想了解繳費流程
- **RD**：開發新功能需要測資
- **SDET**：建立 TestCase 需要的測試情境

如果使用者沒提到自己是哪個角色，預設用 PM 友善口吻（避免術語、用實際業務情境舉例）。

---

## 前置條件

呼叫此 skill 前需確認：

1. **MCP server 連線**：Claude Code 已透過 plugin 的 `.mcp.json` 連到 Self-Mock-Server 的 MCP server（預設 `http://localhost:9000/mcp`）
2. **MCP tools 可用**：以下 tool 名稱可用（若不存在需提示使用者重啟 Claude Code 或檢查 plugin 設定）：
   - 查詢類：`list_services`、`list_routes`、`list_scenarios`、`get_scenario`、`search_scenarios`
   - 變更類：`create_scenario`、`update_scenario`、`delete_scenario`
   - 變更紀錄：`export_change_record`

無法呼叫 MCP tool 時，**不要硬寫 JSON 或猜路徑** — 直接告訴使用者目前連不到 MCP server，請先確認設定。

---

## 開場導覽

每次被呼叫，先顯示：

```
🛠 Self-Mock-Server 場景管理（Session 1）

我可以幫你：
  • 查詢現有 scenario（看看別人有沒有做過類似的）
  • 新增 scenario（描述情境給我，例：「中華電信查繳成功」）
  • 修改 / 刪除 scenario
  • 結束時匯出本次變更（給 RD 帶回本機 repo 套用）

請描述你想做什麼，或先告訴我要操作的服務（例：中華電信 EFCS、台新 NPI）。
```

---

## Step 1：理解使用者意圖

從使用者的描述中辨識三件事：

| 維度 | 說明 | 範例 |
|------|------|------|
| **服務（service）** | 對應到 `configs/<service>/` 目錄 | 中華電信 EFCS → `cht`、凱擘 CNS → `kbro` |
| **操作意圖** | search / create / update / delete / clone / bulk / explore | 「找一下有沒有」= search、「幫我模擬 X」= create、「複製一個改 OO」= clone、「常見情境批次建」= bulk |
| **情境條件** | 成功/失敗/特定錯誤碼/特殊欄位值 | 「查繳失敗，金額為 0」、「退款逾時」 |

**辨識不出時，先用 `list_services` 列出目前平台上所有 service 給使用者選**，不要硬猜。

### 服務名稱對照（references 已收錄者）

| 業務名稱 | 平台 service key（呼叫 `list_services` 看到的） | reference |
|---------|------------|-----------|
| 中華電信 EFCS（台新 / 新光） | `taishin`（config: `taishin/cht.json`） | [cht-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/cht-efcs.md) |
| 凱擘有線電視 CNS | `kbro` | [kbro.md](C:/Workspace/sdet-mock-server/self-mock-server/references/kbro/kbro.md) |
| 台灣大哥大 EFCS | `taishin`（config: `taishin/twm.json`） | [twm-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/twm-efcs.md) |
| 國民年金 NPI（台新 EFCS） | `taishin`（config: `taishin/npi.json`，待 SDET 校對） | [npi-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/npi-efcs.md) |
| 地方稅 LT/LTE（19 縣市，台新 EFCS + 北市移轉案） | `taishin`（config: `taishin/local-tax.json`，待 SDET 校對） | [local-tax-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/local-tax-efcs.md) |
| 臺北市學雜費 TTPE（PayTaipei → 台新 EFCS） | `taishin`（config: `taishin/tuition-tpe.json`，待 SDET 校對） | [taipei-tuition-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/taipei-tuition-efcs.md) |
| 臺北市路邊停車費 PTE/TPE（PayTaipei → 台新 EFCS） | `taishin`（config: `taishin/parking-tpe.json`，待 SDET 校對，**BTYPECLASS=`0307`**） | [parking-tpe-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/parking-tpe-efcs.md) |
| 臺北市自來水水費（PayTaipei → 台新 EFCS，2026/06 上線） | `taishin`（config: `taishin/taipei-water.json`，待 SDET 校對；DR 尚未撰寫） | [taipei-water-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/taipei-water-efcs.md) |
| 瓦斯費（24+ 業者，新光 → 台新 EFCS 2025/09 移轉） | `taishin`（config: `taishin/gas.json`，待校對，**BTYPECLASS=`0104`**） | [gas-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/gas-efcs.md) |
| 汽車代檢費（關貿，台新 EFCS） | `taishin`（config: `taishin/vehicle-inspection.json`，**BTYPECLASS=`0312`**，BILLER_ID=`97162640`） | [vehicle-inspection-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/vehicle-inspection-efcs.md) |
| 汽燃費（本費，監理所，台新 EFCS） | `taishin`（config: `taishin/fuel-fee.json`，**BTYPECLASS=`0302`**，BILLER_ID=`99999801`） | [fuel-fee-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/fuel-fee-efcs.md) |
| 交通違規罰鍰（個人+法人，台新 EFCS） | `taishin`（config: `taishin/fines-traffic.json`，**BTYPECLASS=`0310`**，BILLER_ID=`99999803`，個人 QUERY_TYPE=`1` / 法人 `2`） | [fines-traffic-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/fines-traffic-efcs.md) |
| 違反強制險罰鍰（監理所，台新 EFCS） | `taishin`（config: `taishin/mandatory-insurance-fine.json`，**BTYPECLASS=`0311`**，BILLER_ID=`99999804`） | [mandatory-insurance-fine-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/mandatory-insurance-fine-efcs.md) |
| 中嘉有線電視費 CJBB（13 家業者，台新 EFCS） | `taishin`（config: `taishin/cable-tv-cjbb.json`，待 SDET 校對；DR 空白） | [cable-tv-cjbb-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/cable-tv-cjbb-efcs.md) |
| 凱擘有線電視費（20 家業者，**自家 web API，非 EFCS**） | `kbro`（config: `kbro/{bind,payment,query_bill}.json`） | [kbro.md](C:/Workspace/sdet-mock-server/self-mock-server/references/kbro/kbro.md) ← 已補強 PMOLD PRD 內容 |
| 全民健保費（**健保署直串，非 EFCS**） | `nhi`（推測 config: `nhi/{query_bill,pay,bind_notify,query_notify}.json`） | [nhi-direct.md](C:/Workspace/sdet-mock-server/self-mock-server/references/nhi/nhi-direct.md) |
| 台灣自來水公司（**直串台水 API，非 EFCS**） | `tw-water`（推測 config: `tw-water/{query_bill,pay,bind,unbind,notify}.json`） | [tw-water-direct.md](C:/Workspace/sdet-mock-server/self-mock-server/references/tw-water/tw-water-direct.md) |
| 台電（**直串台電 API，非 EFCS，自 2019/12 上線**） | `tw-power`（推測 config: `tw-power/{bind_check,query_bill,selection_notify,pay_notify,cancel,push}.json`） | [tw-power-direct.md](C:/Workspace/sdet-mock-server/self-mock-server/references/tw-power/tw-power-direct.md) |
| **公路局 hub**（5 個店鋪：汽燃費本費/違費、交通罰鍰個人/法人、違反強制險罰鍰，走 EFCS） | 共用 `taishin/` 或 `skb/`（**通道移轉中**），靠 BILLER_ID 區分 | [highway-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/highway-efcs.md) — hub；業者專屬細節見 [fuel-fee-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/fuel-fee-efcs.md) / [fines-traffic-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/fines-traffic-efcs.md) / [mandatory-insurance-fine-efcs.md](C:/Workspace/sdet-mock-server/self-mock-server/references/taishin/mandatory-insurance-fine-efcs.md) |

> ⚠️ 「業務名稱」與「平台 service key」常常不同。例：使用者口中的「中華電信」對應到 mock 平台是 `taishin`（因為走台新 EFCS 通道），不是 `cht`。識別意圖時要先做這層映射，**不要直接拿業務名稱去呼叫 MCP**。

> 要查的服務不在表格內 → 用 `list_services` 看平台上實際有什麼，再告訴使用者「目前沒有對應的 reference 文件，我會用通用流程建立，但欄位細節可能需要你或後端確認」。

### Reference 缺漏早偵測（建立 / 修改前必跑）

辨識到 service 是 create / update 意圖時，**進 Step 2 之前**先快掃 reference：

| 檢查項 | 缺漏處理 |
|-------|---------|
| `C:/Workspace/sdet-mock-server/self-mock-server/references/<service-key>/*.md` 存在 | 不存在 → ⚠️ 提示使用者：「無 reference，建議先呼叫 `/self-mock-reference-gen` 產文件再回來建 scenario，避免欄位猜錯」。仍可選擇強制繼續，但後續欄位細節得使用者自行擔保。 |
| 文件 `<待補>` 數量 | > 5 處 → ⚠️ 顯示「reference 多處待補，建立的 scenario 可能 schema 不正確」 |
| 「常見測試情境」章節有內容 | 無 → 提示「reference 缺『常見測試情境』表格，無法用 `/self-mock-bulk-scenarios` 一鍵建」 |

**search / explore / delete 意圖** → 不需要這個檢查，跳過。

### 跨 service 模糊搜（無法定位 service 時的後備）

使用者描述太模糊（例「找看看有沒有金額為 0 的情境」、「退款失敗的情境」）無法鎖定 service 時，**不要逼使用者選 service**，改走跨 service 搜：

呼叫 `search_scenarios(query=<關鍵字>)`（不帶 service 參數，平台側全域搜）→ 結果按 service 分組顯示：

```
🔎 跨 service 搜尋「金額為 0」找到 4 個 scenario：

  cht/
    • cht-pay-fail-amount-zero      （POST /ebpp/cht/api/v1/order）
    • cht-query-amount-zero         （GET  /ebpp/cht/api/v1/ebill）
  
  kbro/
    • kbro-cns-amount-zero          （POST /ebpp/kbro/cns/api/v1/order）

  taishin/
    • taishin-cht-pay-zero          （POST /o360/webservice/EFCS）

要看哪個的詳情？或繼續搜尋？
```

`search_scenarios` 不可用 → 退而求其次：對 `list_services()` 結果逐個跑 `list_scenarios(service)` 後在本端 grep，但**最多查 5 個 service**避免 N+1。

---

## Step 2：載入 reference + 查現況

確認服務後，並行執行：

1. **讀對應 reference**（若有）：取得 endpoint、欄位定義、常見情境、銀行代碼等
2. **`list_routes(service)`**：看該服務目前有哪些 route
3. **`search_scenarios(query=<關鍵字>)`** 或 **`list_scenarios(service, route, method)`**：看有沒有現成的可以重用

把結果摘要展示給使用者：

```
📂 服務：中華電信 EFCS（cht）

現有 routes：
  • POST /ebill/fromServer/  （轉址繳費，B101/B102/B105）
  • POST /ebpp/isv/cht/api/v1/refund  （退款，B107）

跟你描述相近的 scenario：
  • cht-query-success（B101 查繳成功）  
  • cht-pay-fail-amount-zero（B102 繳費失敗，金額為 0）

要重用哪一個？還是要我新建一個？
```

**重用優先**（roadmap 第二目標：把測資變資產）。確實沒有相符的再進入 Step 3 建立。

---

## Step 3：收集 mutation 必要資訊（建立 / 修改）

**一次問一題，不要一次列所有問題。** 只問 reference 沒有預設值、又必要的東西。

### 建立 scenario 時必問

1. **scenario 名稱**：建議格式 `<service>-<route>-<intent>`，例 `cht-query-success-empty-bill`
2. **觸發條件**：在什麼 request 條件下會命中此 scenario？（mock server 的核心匹配邏輯）
3. **回應內容**：
   - 若 reference 有「常見測試情境」對應條目 → 直接套用，跟使用者確認即可
   - 若沒有 → 問 status code、關鍵欄位值；其餘從 reference 預設

### 修改 scenario 時必問

1. 要改的 scenario 名稱（從 Step 2 列表中選）
2. 要改哪些欄位（response / 條件 / 名稱）

### 刪除 scenario 時必問

1. 確認 scenario 名稱（從 Step 2 列表中選）
2. **二次確認**：「確定要刪除 `<name>` 嗎？此操作會寫入 config 檔。」

### Pre-Action Micro-Checklist（呼叫 mutation tool 前在心裡跑一遍）

不同動作有不同必檢項；漏一項就可能撞既有 scenario、覆蓋意外、或 race 別人寫的東西。

**create**
- ☐ 已用 `list_scenarios` 確認新名稱不撞既有
- ☐ 唯一性欄位已避撞（例：EFCS 系統的 `EFCSSEQNO`、訂單系統的 trace id；任一個被多 scenario 撞同樣值，會讓後續查單對不上）
- ☐ 條件夠精確以致不會誤命中既有成功路徑（特別是 default 排序在後的 service）

**update**
- ☐ 已 `get_scenario` 抓現況做為 4.4 undo 紀錄
- ☐ **`update_scenario` 是整顆 scenario 替換，不是 patch** — 一定要先 `get_scenario` 然後在拿到的 JSON 上改，再整顆送回
- ☐ 修改的條件不會把原本命中此 scenario 的測資推到 default

**delete**
- ☐ 已 `get_scenario` 抓完整 JSON 做 undo
- ☐ 已 grep 過 `configs/` 看其他 service 是否依賴同樣 condition pattern（跨 service 同 path 共用時特別重要，例如台新 EFCS `/o360/webservice/EFCS` 16 個 service 共用）
- ☐ 二次確認句 + 顯示被刪除的完整內容

---

## Step 4：預覽 + 確認

呼叫 mutation tool 之前，**一定先給使用者預覽**。預覽分**兩層**：先給人話摘要，再給 JSON-level diff（避免「我以為改了 A 結果改到 B」）。

### 4.1 摘要層（給人讀）

```
即將執行：create_scenario

  service: cht
  route:   POST /ebill/fromServer/
  name:    cht-query-success-empty-bill
  
  條件：billNo 開頭為 "TEST-EMPTY"
  回應：HTTP 200，bills 陣列為空（模擬無待繳帳單）
```

### 4.2 JSON Diff 層（給機器精確核對）

**create**：直接顯示完整 scenario JSON（會新增的內容）。

**update**：先 `get_scenario(name=<舊>)` 取現況，與將寫入的版本做 unified diff。⚠️ **`update_scenario` 是整顆替換不是 patch**：把 `get_scenario` 拿到的完整 JSON 修改後整顆送回，避免漏帶欄位導致 scenario 失去 condition 或 response 結構：

```
🔬 JSON Diff（舊 → 新）

  {
    "name": "cht-pay-success-skb",
    "match": {
-     "body.amount": "> 0"
+     "body.amount": ">= 0"
    },
    "response": {
-     "status_code": 200,
+     "status_code": 200,
      "body": {
-       "result": "success"
+       "result": "success",
+       "trace_id": "auto"
      }
    }
  }
```

**delete**：顯示即將被刪除的完整 scenario（給使用者最後確認）。

### 4.3 確認

```
確認執行嗎？
  (y) 是，呼叫 mutation tool
  (n) 否，回到 Step 3 修改
  (j) 顯示完整 JSON 而非 diff
  (s) 跳過此筆，繼續下一個（僅在 bulk flow 適用）

請選擇：
```

使用者選 `y` / `是` / `確認` 才實際呼叫 MCP mutation tool。

### 4.4 寫入後保留 undo 紀錄

每次成功 mutation **暫存反向操作**到當前 session 記憶（**不寫檔，僅在對話 context 內**）：

| 原操作 | 反向 |
|-------|------|
| `create_scenario(name=X, ...)` | `delete_scenario(name=X)` |
| `update_scenario(name=X, new=...)` | `update_scenario(name=X, new=<舊版本>)`（用 4.2 抓的舊 JSON）|
| `delete_scenario(name=X)` | `create_scenario(...)`（用刪除前 get 到的完整 JSON）|

最多保留**最近 5 筆**。使用者說「undo」/「回上一步」/「reverse 剛剛的」→ 列出可 undo 清單，二次確認後呼叫對應 inverse mutation。

```
🔄 Undo 清單（最近 5 筆，最新在上）

  1. create_scenario(cht-pay-fail-new)        @ 2 分鐘前  → 反向：delete
  2. update_scenario(cht-query-success)        @ 5 分鐘前  → 反向：update 回舊版
  3. delete_scenario(cht-pay-old)              @ 8 分鐘前  → 反向：create

要 undo 第幾筆？(1-3 / cancel)
```

⚠️ **跨 session 不保留 undo**（context 重置就清掉）。對使用者明示這點。

### 緊急回退（救得回 vs 救不回）

**救得回**（同一 session、5 筆內、有抓到舊 JSON）：用上面 4.4 的 undo 清單。

**救不回**（任一條件不滿足）：

| 情況 | 為什麼救不回 | 怎麼辦 |
|---|---|---|
| 跨 session（context 已 reset） | undo log 是對話記憶，新 session 看不到 | 開 `self-mock-diff-envs` 比對 SIT 與本機 clone；或從 `self-mock-snapshot` 復原 |
| 已超過 5 筆 | 只保留最近 5 筆 | 同上 |
| `update` 沒先 `get_scenario` | 沒抓到舊 JSON 就沒法反向 | 從 `self-mock-snapshot` 的最近一次匯出復原；沒匯出 → 真的救不回，需要憑記憶 / git history 重建 |
| 對方 service 直接被 `delete` 且未存舊 JSON | 同上 | 同上 |

> ⚠️ **mock server config 不一定有 git history 對齊**（測試環境 = 共用平台，使用者改了不一定有 commit）— 不能假設「revert 到上個 commit」就好。

讓使用者清楚知道「我這個 session 救得回什麼、跨 session 救不回什麼」，是 mutation 工具的核心責任。

### Mutation 失敗處理

| 情況 | 處理 |
|------|------|
| Validator 失敗 | 顯示完整 error list，**不重試**，回到 Step 3 修正後重新預覽 |
| Scenario / route 不存在（update / delete 時） | 顯示 not found + 候選名稱（MCP tool 自帶 Levenshtein 建議），讓使用者選 |
| IO error | 顯示錯誤、告知未寫入，建議使用者稍後重試 |

**遇到驗證失敗不要自己亂猜欄位填值** — 直接問使用者，避免污染測試環境。

---

## Step 5：結尾與 handoff

使用者完成所有操作（包含「不要再做了」）後：

1. 提示匯出變更紀錄
2. 引導下一步（Session 2，本機套用）

```
✅ 本次操作完成！

要匯出變更紀錄給 RD 帶回本機 repo 嗎？

  (a) 是，呼叫 export_change_record（建議）
  (b) 否，只在測試環境留著

請選擇：
```

選 (a) → 呼叫 `export_change_record`，把回傳的 markdown **完整貼到對話**（不是寫成檔），並告訴使用者：

```
📄 變更紀錄如上。

下一步（Session 2）：
  1. 把上面的 markdown 存成檔案，例：~/change-record-<date>.md
  2. 切到本機 clone 的 self-mock-server 目錄
  3. 開新的 Claude Code session，呼叫 /self-mock-apply-change-record
     會自動 replay 操作到本機 configs/、產 MR description、印 git 指令
  4. git diff 自己 review，確認後 push 發 MR

⚠️ 若 export_change_record 回傳了 Concurrency Notice，代表有其他 session
   也在改同一個檔案，套用前務必人工確認。
```

如果 export 沒有 Concurrency Notice，最後一行警告省略。

---

## 跨 service 操作模式

> 這節是對 CRUD 操作的補充：當使用者的需求牽涉到多個 service / 跨 message 的關聯時，如何不踩到其他 service 的 scenario。

### Mode A — 同 service 內 B101 → B102 的 BILLDATA 關聯（EFCS 系列）

EFCS 系列（CHT、cns_cable_tv、kbro、台新 NPI 等）裡，B101（查單）的 response BILLDATA 會被使用者帶回成 B102（銷案）的 request BILLDATA。**設計 mock 時要讓 B101 的某個 scenario 跟 B102 的某個 scenario「BILLDATA 字串對得起來」**。

- 建立失敗版 B102 時：拿一個跟成功版 B102 不同尾碼的 BILLDATA，避免命中錯
- 建立失敗版 B101 時：response BILLDATA 要對應到一個真的有實作的 B102 scenario（不然測試套件繼續打 B102 就會 fallback 到 default）

### Mode B — 同 path 跨 service 不混 scenario

台新 EFCS 的 `/o360/webservice/EFCS` 16 個 service 共用路由，scenario 全部塞在 `taishin/<service>.json`，但實際匹配是「同個 endpoint 把所有 scenario 列出來逐一比 conditions」。

- 寫 condition 一定帶 service 區分欄位（`DOCDATA.HEAD.BTYPECLASS`，或對應的 `BILLER_ID`）
- 不要寫只比 `PRS_CODE=B102` 就決定路由的 condition — 會誤命中其他 service
- 建立前 grep 一遍其他 service 的 scenario，確保 condition 集合是不相交的

### Mode C — 一個 method 只允許一個 default

每個 (service, route, method) 三元組的 scenarios array 裡，`is_default: true` 只能有一個（fallback）。

- 新增 default 之前：用 `list_scenarios` 確認沒有既存 default
- 若使用者描述像「兜底場景」「沒命中時回什麼」→ 那就是 default，不是新 scenario
- 撞到既存 default：要嘛改既有 default 的內容，要嘛把新需求做成有 condition 的明確 scenario

---

## 行為原則

- **不假裝懂業務**：reference 沒寫的欄位 → 問使用者或後端，不要編造
- **不擴大範圍**：使用者只要改 A scenario 就改 A，不順手調 B
- **不寫檔到 self-mock-server repo**：所有 scenario 變更都透過 MCP tool（會原子寫入 + 自動 reload）
- **不執行 git 操作**：MCP server 沒有 git 憑證，git push / 發 MR 屬於 Session 2 流程
- **遇到 reference 缺漏**：若使用者手上有 PRD / Design Review wiki 連結，建議呼叫 `/self-mock-reference-gen` 自動產一份；若只是少量欄位缺漏，引導使用者直接補到 `C:/Workspace/sdet-mock-server/self-mock-server/references/<service-key>/<name>.md`
- **加密 scenario 主動 flag**：若新建 / 修改的 scenario 有 `taishin_encryption: true`（或其他加密旗標），Step 6 的驗證提示一定要警告「**不能直接 curl 明文 — 請走團隊既有加密測試工具**」，使用者沒問也要主動講
- **不要用「delete + create」替代 update**：兩個動作之間有 race window，watchdog reload 可能跑進測試流程造成短暫 default fallback。需要改既有 scenario 一律用 `update_scenario`

---

## 相關 skills（轉介路由）

依使用者意圖適時引導，不替使用者自動啟動：

| 意圖 | Skill |
|------|-------|
| 「這個 scenario 為什麼沒命中我的 request」 | `/self-mock-trace` |
| 「我有真實 log，幫我反向產 scenario」 | `/self-mock-from-trace` |
| 「複製這個 scenario 改幾個欄位」 | `/self-mock-clone` |
| 「reference 的常見測試情境一鍵全建」 | `/self-mock-bulk-scenarios` |
| 「比較 SIT 跟本機的差異」 | `/self-mock-diff-envs` |
| 「scenario 太亂幫我整理 / lint」 | `/self-mock-lint` |
| 「環境檢查 / MCP 是否正常」 | `/self-mock-health-check` |
| 「新 service 要建 reference」 | `/self-mock-reference-gen` |
| 「把測試環境變更套回本機開 MR」 | `/self-mock-apply-change-record` |
| 「snapshot 整個平台 / 還原備份」 | `/self-mock-snapshot` |
| 「哪些 scenario 沒人用 / coverage 報告」 | `/self-mock-coverage` |
| 「base on X 產一堆邊界值變體 / fuzz」 | `/self-mock-fuzz` |
| 「整份 HAR / 多筆 trace 批次轉 scenario」 | `/self-mock-from-trace`（bulk mode） |
| 「從 PRD 一口氣端到端把整套 scenario 建好」 | `scenario-builder` agent |
