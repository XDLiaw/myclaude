---
name: excel-comparator
description: 批次比對 Excel 檔案內容是否一致，包含呈現形式、小數點位數、時間格式等。當需要比對兩個 Excel 檔案差異、驗證資料匯出結果、檢查報表一致性時使用。支援生成詳細差異報告。
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# Excel Comparator Skill

批次比對 Excel 檔案內容，生成詳細差異報告。

## 腳本位置

```
~/.claude/skills/excel-comparator/excel_comparator.py
```

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "比對兩個 Excel 檔案"
- "檢查 Excel 差異"
- "驗證 Excel 匯出結果"
- "比較報表是否一致"
- "Excel 格式是否相同"
- "檢查小數點位數"
- "比對時間格式"

## 比對項目

| 類別 | 項目 | 說明 |
|------|------|------|
| **值** | 文字 | 字串內容比對 |
| **值** | 數字 | 支援容差設定 |
| **值** | 日期時間 | datetime 物件比對 |
| **格式** | 小數點位數 | `0.00` vs `0.0000` |
| **格式** | 日期格式 | `yyyy-mm-dd` vs `mm/dd/yyyy` |
| **格式** | 百分比 | `0.5` vs `50%` |
| **格式** | 貨幣 | `100` vs `$100` |
| **樣式** | 字型 | 名稱、大小、粗體、斜體 |
| **樣式** | 顏色 | 文字色、背景色 |
| **樣式** | 對齊 | 水平、垂直對齊 |

## 執行指令

### 基本比對

```bash
python ~/.claude/skills/excel-comparator/excel_comparator.py "file1.xlsx" "file2.xlsx"
```

### 常用參數

```bash
# 指定輸出路徑
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx -o report.md

# 輸出 JSON 格式
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx --format json

# 包含樣式比對
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx --styles

# 設定數值容差（忽略小於 0.01 的差異）
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx --tolerance 0.01

# 只比對特定工作表
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx --sheets Sheet1 Summary

# 比對公式而非計算值
python ~/.claude/skills/excel-comparator/excel_comparator.py file1.xlsx file2.xlsx --formulas
```

## 參數說明

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `file1` | 第一個 Excel 檔案 | (必填) |
| `file2` | 第二個 Excel 檔案 | (必填) |
| `-o, --output` | 輸出報告路徑 | comparison_report.md |
| `--format` | 報告格式 (md/json) | md |
| `--no-values` | 不比對值 | False |
| `--no-formats` | 不比對格式 | False |
| `--styles` | 比對樣式 | False |
| `--formulas` | 比對公式 | False |
| `--tolerance` | 數值容差 | 1e-10 |
| `--sheets` | 指定工作表 | 全部 |

## 輸出報告格式

### Markdown 報告包含

1. **基本資訊** - 檔案路徑、比對時間、儲存格數
2. **工作表差異** - 僅存在於單一檔案的工作表
3. **差異摘要** - 按類型統計差異數量
4. **詳細差異** - 每個工作表的差異清單（限 100 筆）
5. **結論** - 是否一致、差異總數

### Exit Code

- `0`: 兩檔案完全一致
- `1`: 發現差異

## 執行流程

1. **收集檔案路徑** - 確認使用者要比對的兩個 Excel 檔案
2. **確認比對選項** - 是否需要比對樣式、設定容差等
3. **執行比對** - 呼叫 excel_comparator.py
4. **讀取並顯示報告** - 顯示差異摘要和重點差異

## 依賴套件

```bash
pip install openpyxl
```

## 注意事項

1. **檔案格式**: 僅支援 `.xlsx`（Excel 2007+）
2. **效能**: 大檔案（>10 萬儲存格）需較長時間
3. **格式比對**: 比對 Excel 內部格式代碼，非顯示結果
4. **數值精度**: 預設容差 1e-10 可處理浮點數精度問題
