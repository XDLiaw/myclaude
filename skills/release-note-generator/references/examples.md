# 互動式流程範例

兩個完整的互動範例，展示從 Git 分析到生成文件的對話流程與輸出樣貌。範本定義見 `references/templates.md`。

## 目錄
- [範例 1：只產 Release Note](#範例-1只產-release-note)
- [範例 2：Release Note + 上版計畫](#範例-2release-note--上版計畫)

---

## 範例 1：只產 Release Note

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

## 範例 2：Release Note + 上版計畫

```
User: "幫我產生 release note 和上版計畫，commit 是 abc1234，rollback 是 def5678，預計 2025/03/01 上版"

Claude (使用此 Skill):
好的，我將根據這兩個 commit 生成 Release Note 和上版計畫。

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

📄 生成上版計畫...

---

## 上版前準備

| Team / PIC | Description | Note / Ticket |
|------------|-------------|---------------|
| RD3 | DB 異動申請 | 新增 insurance_order_refund table |
| RD3 | Vault 設定申請 | refund_api_key |

## 上版計畫

| Order | Team / PIC | Service | Release Date | Note / Ticket |
|-------|------------|---------|--------------|---------------|
| 1 | RD3 | jkopay-insurance | 2025/03/01 | |

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
- Release Note 將建立在父頁面下
- 上版計畫將建立在 Release Note 頁面下
```
