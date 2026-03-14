---
name: jobdata-encoder
description: 將 JSON 格式的 Argo Workflow job 參數編碼為 base64，或將 base64 字串解碼為 JSON。當需要設定 jobData、編碼 job 參數、或查看現有 jobData 內容時使用。支援驗證 JSON 格式和 jobName 一致性檢查。
allowed-tools:
  - Bash
  - Read
---

# JobData Encoder Skill

專門處理 Argo Workflow Schedule Job 的 `jobData` 參數編碼與解碼。

## 核心功能

1. **JSON 到 Base64 編碼** - 將 job 參數轉換為可用的 base64 字串
2. **Base64 到 JSON 解碼** - 查看現有 jobData 的實際內容
3. **JSON 格式驗證** - 確保 JSON 結構正確
4. **jobName 提醒** - 提醒使用者確認 jobName 與 Java code 一致

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "幫我編碼 jobData"
- "將這個 JSON 轉成 base64"
- "解碼這個 base64 jobData"
- "查看 jobData 內容"
- "這個 base64 代表什麼參數"
- "生成 Argo job 參數"

## jobData 格式說明

### 標準結構

Argo Workflow 的 jobData 必須包含以下結構：

```json
{
  "jobName": "Java類別名稱",
  "parameter": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

### 欄位說明

#### jobName (必填)
- **用途**: 指定要執行的 Java job 類別
- **規則**: 必須與 Java code 中 `getJobName()` 方法的回傳值**完全一致**
- **範例**: `"InsuranceWriteOffJob"`, `"DailySettlementJob"`

#### parameter (選填)
- **用途**: 傳遞給 job 的參數
- **類型**: JSON 物件，會被 deserialize 到 Java job 的參數物件
- **範例**:
  ```json
  {
    "batchSize": "1000",
    "retryCount": "3",
    "enabled": true,
    "dateRange": ["2024-01-01", "2024-01-31"]
  }
  ```

### 實際範例

#### 範例 1: 簡單參數

```json
{
  "jobName": "DailyReportJob",
  "parameter": {
    "date": "today"
  }
}
```

#### 範例 2: 複雜參數

```json
{
  "jobName": "InsuranceLegacyRetryWriteOffJob",
  "parameter": {
    "batchSize": "100",
    "maxRetries": "3",
    "enabled": true,
    "filters": {
      "status": "pending",
      "dateFrom": "2024-01-01"
    }
  }
}
```

#### 範例 3: 無參數

```json
{
  "jobName": "SimpleCleanupJob",
  "parameter": {}
}
```

## 編碼功能

### 輸入格式

使用者可以提供：

1. **完整 JSON 字串**:
   ```
   {"jobName":"MyJob","parameter":{"key":"value"}}
   ```

2. **分別提供欄位**:
   ```
   - jobName: MyJob
   - parameters: {"key":"value"}
   ```

3. **互動式輸入**:
   Claude 逐步詢問 jobName 和 parameters

### 處理流程

1. **接收輸入**
   - 解析使用者提供的 JSON 或欄位

2. **驗證 JSON 格式**
   - 檢查 JSON 語法正確性
   - 確認 `jobName` 欄位存在且非空
   - 驗證 `parameter` 是物件（如果提供）

3. **格式化 JSON**
   - 移除不必要的空白（minify）
   - 確保使用雙引號

4. **Base64 編碼**
   - 使用 `echo -n` 避免換行符
   - 執行 `base64` 編碼

5. **輸出結果**
   - 顯示原始 JSON（格式化，易讀）
   - 顯示編碼後的 base64 字串
   - 提供 jobName 一致性檢查提醒

### 編碼指令

```bash
# 標準編碼（最重要：使用 -n 避免換行符）
echo -n '{"jobName":"MyJob","parameter":{"key":"value"}}' | base64
```

**重要提醒**:
- ✅ **必須使用 `echo -n`** - 避免在 JSON 後添加換行符
- ❌ **不要使用 `echo`** - 會添加換行符導致編碼錯誤

### 輸出範例

```markdown
## 編碼結果

### 原始 JSON (格式化)
```json
{
  "jobName": "DailyReportJob",
  "parameter": {
    "date": "today",
    "format": "pdf"
  }
}
```

### Base64 編碼
```
ewogICJqb2JOYW1lIjogIkRhaWx5UmVwb3J0Sm9iIiwKICAicGFyYW1ldGVyIjogewogICAgImRhdGUiOiAidG9kYXkiLAogICAgImZvcm1hdCI6ICJwZGYiCiAgfQp9
```

### 使用方式

在 Schedule Job YAML 中:
```yaml
arguments:
  parameters:
    - name: jobData
      value: ewogICJqb2JOYW1lIjogIkRhaWx5UmVwb3J0Sm9iIiwKICAicGFyYW1ldGVyIjogewogICAgImRhdGUiOiAidG9kYXkiLAogICAgImZvcm1hdCI6ICJwZGYiCiAgfQp9
```

### ⚠️ 重要提醒

確認 `jobName: "DailyReportJob"` 與 Java code 中的 `getJobName()` 回傳值完全一致：

```java
public class DailyReportJob implements Job {
    @Override
    public String getJobName() {
        return "DailyReportJob";  // 必須完全相符
    }
}
```
```

---

## 解碼功能

### 輸入格式

使用者可以提供：

1. **Base64 字串**:
   ```
   ewogICJqb2JOYW1lIjogIk15Sm9iIgp9
   ```

2. **從檔案讀取**:
   ```
   從 rd3/jkopay-insurance/...sj.patch.yaml 解碼 jobData
   ```

### 處理流程

1. **接收 Base64 字串**
   - 從使用者訊息或檔案中提取

2. **Base64 解碼**
   - 執行 `base64 --decode`

3. **驗證 JSON**
   - 檢查解碼結果是否為有效 JSON
   - 驗證必要欄位存在

4. **格式化輸出**
   - 以易讀格式顯示 JSON
   - 高亮關鍵欄位（jobName, parameter）

5. **提供說明**
   - 解釋各參數用途
   - 提醒 jobName 一致性

### 解碼指令

```bash
# 標準解碼
echo 'base64-string' | base64 --decode

# 解碼並格式化（如果有 jq）
echo 'base64-string' | base64 --decode | jq .
```

### 輸出範例

```markdown
## 解碼結果

### Base64 字串
```
ewogICJqb2JOYW1lIjogIkluc3VyYW5jZVdyaXRlT2ZmSm9iIiwKICAicGFyYW1ldGVyIjogewogICAgImJhdGNoU2l6ZSI6ICIxMDAwIgogIH0KfQ==
```

### JSON 內容
```json
{
  "jobName": "InsuranceWriteOffJob",
  "parameter": {
    "batchSize": "1000"
  }
}
```

### 參數說明

- **jobName**: `InsuranceWriteOffJob`
  - 執行的 Java job 類別名稱
  - ⚠️ 必須與 Java code 中的 `getJobName()` 回傳值一致

- **parameter**:
  - `batchSize`: `"1000"` - 每批次處理數量

### Java Code 對照

確認此 jobName 對應的 Java 類別：

```java
public class InsuranceWriteOffJob implements Job {
    @Override
    public String getJobName() {
        return "InsuranceWriteOffJob";  // ✅ 與 jobData 一致
    }

    // Parameter 會被 deserialize 到這個物件
    public static class Parameter {
        private String batchSize;
        // getters and setters...
    }
}
```
```

---

## JSON 驗證功能

### 驗證項目

1. **語法正確性**
   - 檢查是否為有效 JSON
   - 檢查括號、引號匹配

2. **結構完整性**
   - 必須包含 `jobName` 欄位
   - `jobName` 不可為空字串
   - `parameter` 必須是物件（如果提供）

3. **類型檢查**
   - 確認各欄位類型正確
   - 數字、布林值、陣列格式

4. **常見錯誤偵測**
   - 單引號（應使用雙引號）
   - 尾隨逗號
   - 未引用的 key
   - 特殊字元未跳脫

### 驗證輸出

#### 成功範例
```markdown
✅ JSON 驗證通過

結構:
- jobName: "MyJob" ✅
- parameter: { ... } ✅

準備編碼...
```

#### 失敗範例
```markdown
❌ JSON 驗證失敗

錯誤: Unexpected token at line 2, column 5

問題:
```json
{
  'jobName': 'MyJob'  // ❌ 使用單引號
}
```

修正:
```json
{
  "jobName": "MyJob"  // ✅ 使用雙引號
}
```
```

---

## 互動式使用範例

### 範例 1: 快速編碼

```
User: "幫我編碼 jobData: jobName 是 DailyJob, parameter 是 {date: today}"

Claude: [啟用 jobdata-encoder Skill]

我將為您編碼 jobData。

首先讓我驗證 JSON 格式...

✅ JSON 驗證通過

原始 JSON:
{
  "jobName": "DailyJob",
  "parameter": {
    "date": "today"
  }
}

執行編碼...

✅ 編碼完成！

Base64 結果:
ewogICJqb2JOYW1lIjogIkRhaWx5Sm9iIiwKICAicGFyYW1ldGVyIjogewogICAgImRhdGUiOiAidG9kYXkiCiAgfQp9

⚠️ 重要提醒:
請確認 Java code 中的 getJobName() 回傳 "DailyJob"
```

### 範例 2: 互動式編碼

```
User: "生成 Argo job 參數"

Claude: [啟用 jobdata-encoder Skill]

我將協助您生成 Argo Workflow jobData 參數。

請提供以下資訊:

1️⃣ Job Class 名稱 (Java code 中的 getJobName() 回傳值):

User: "InsuranceBatchJob"

Claude:
收到 jobName: "InsuranceBatchJob"

2️⃣ Job 參數 (JSON 格式，沒有參數請輸入 {}):

User: {"batchSize": "500", "enabled": true}

Claude:
收到 parameters。

讓我驗證並編碼...

✅ JSON 驗證通過

完整 JSON:
{
  "jobName": "InsuranceBatchJob",
  "parameter": {
    "batchSize": "500",
    "enabled": true
  }
}

✅ Base64 編碼:
ewogICJqb2JOYW1lIjogIkluc3VyYW5jZUJhdGNoSm9iIiwKICAicGFyYW1ldGVyIjogewogICAgImJhdGNoU2l6ZSI6ICI1MDAiLAogICAgImVuYWJsZWQiOiB0cnVlCiAgfQp9

您可以將此 base64 字串用於 Schedule Job 的 jobData 參數。
```

### 範例 3: 解碼查看

```
User: "這個 base64 是什麼意思: ewogICJqb2JOYW1lIjogIlRlc3RKb2IiCn0="

Claude: [啟用 jobdata-encoder Skill]

讓我為您解碼這個 jobData。

執行解碼...

✅ 解碼成功！

JSON 內容:
{
  "jobName": "TestJob"
}

參數說明:
- jobName: "TestJob" - 執行 TestJob 類別
- parameter: (未提供) - 此 job 不需要額外參數

對應的 Java 類別應該是:
public class TestJob implements Job {
    @Override
    public String getJobName() {
        return "TestJob";
    }
}
```

### 範例 4: 從檔案解碼

```
User: "幫我查看 rd3/jkopay-insurance 的 legacy-retry-write-off-sj.patch.yaml 裡的 jobData 是什麼"

Claude: [啟用 jobdata-encoder Skill]

讓我讀取該檔案並解碼 jobData...

[讀取檔案]

找到 jobData 參數:
ewogICJqb2JOYW1lIjogIkluc3VyYW5jZUxlZ2FjeVJldHJ5V3JpdGVPZmZKb2IiLAogICJwYXJhbWV0ZXIiOiB7CiAgICAicmV0cnlDb3VudCI6ICIzIgogIH0KfQ==

解碼結果:

{
  "jobName": "InsuranceLegacyRetryWriteOffJob",
  "parameter": {
    "retryCount": "3"
  }
}

此 job 會執行 InsuranceLegacyRetryWriteOffJob，並設定 retryCount 為 3。
```

---

## 錯誤處理

### 編碼錯誤

#### 無效 JSON
```markdown
❌ JSON 格式錯誤

輸入: {jobName: "Test"}

問題: Key 沒有使用雙引號

修正後:
{"jobName": "Test"}

是否使用修正後的 JSON？(yes/no)
```

#### 缺少 jobName
```markdown
❌ jobData 驗證失敗

錯誤: 缺少必填欄位 "jobName"

您提供的 JSON:
{
  "parameter": {
    "key": "value"
  }
}

jobData 必須包含 "jobName" 欄位，用於指定要執行的 Java job 類別。

請提供 jobName:
```

### 解碼錯誤

#### 無效 Base64
```markdown
❌ Base64 解碼失敗

輸入: invalid-base64-string!!!

可能原因:
1. 不是有效的 base64 字串
2. 字串被截斷或損壞
3. 包含不允許的字元

請確認您提供的 base64 字串是否正確。
```

#### 解碼後非 JSON
```markdown
❌ 解碼成功但內容不是 JSON

Base64 解碼結果:
This is plain text, not JSON

此 base64 字串不包含 jobData，可能是其他類型的資料。
```

---

## 快速參考

### 編碼指令
```bash
# 正確方式（使用 -n）
echo -n '{"jobName":"MyJob","parameter":{}}' | base64

# 錯誤方式（缺少 -n）
echo '{"jobName":"MyJob","parameter":{}}' | base64  # ❌ 會包含換行符
```

### 解碼指令
```bash
# 標準解碼
echo 'base64-string' | base64 --decode

# 解碼並格式化
echo 'base64-string' | base64 --decode | python -m json.tool
```

### JSON 最小結構
```json
{
  "jobName": "類別名稱"
}
```

### JSON 完整結構
```json
{
  "jobName": "類別名稱",
  "parameter": {
    "key1": "value1",
    "key2": 123,
    "key3": true,
    "key4": ["array", "values"]
  }
}
```

---

## 最佳實踐

### 1. 確保 jobName 一致性

**在編碼前**:
```
⚠️ 重要檢查清單:

[ ] 確認 Java code 中有對應的 Job 類別
[ ] 確認 getJobName() 回傳值與 jobData 完全一致（大小寫敏感）
[ ] 確認 parameter 結構與 Java Parameter 物件匹配
```

### 2. 參數類型對應

| JSON 類型 | Java 類型 | 範例 |
|----------|----------|------|
| `"string"` | `String` | `"value"` |
| `number` | `Integer`, `Long`, `Double` | `123`, `3.14` |
| `boolean` | `Boolean` | `true`, `false` |
| `array` | `List`, `Array` | `["a", "b"]` |
| `object` | Custom Object | `{"key": "value"}` |

### 3. 常見參數命名

| 參數名稱 | 用途 | 範例值 |
|---------|------|--------|
| `batchSize` | 批次處理數量 | `"1000"` |
| `retryCount` | 重試次數 | `"3"` |
| `enabled` | 是否啟用 | `true` |
| `date` | 執行日期 | `"2024-01-01"`, `"today"` |
| `dateFrom`, `dateTo` | 日期範圍 | `"2024-01-01"` |

### 4. 測試編碼結果

編碼後建議測試：
```bash
# 編碼
ENCODED=$(echo -n '{"jobName":"Test"}' | base64)

# 立即解碼驗證
echo $ENCODED | base64 --decode

# 應該顯示原始 JSON
```

---

## 總結

此 Skill 提供：
- ✅ 快速 JSON ↔ Base64 轉換
- ✅ JSON 格式驗證
- ✅ jobName 一致性提醒
- ✅ 互動式輸入支援
- ✅ 從檔案讀取解碼
- ✅ 詳細的錯誤處理
- ✅ Java code 對照說明

讓團隊成員輕鬆處理 Argo Workflow jobData 參數，無需手動執行 bash 指令。
