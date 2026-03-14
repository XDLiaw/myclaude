---
name: confluence-mermaid
description: 將 Mermaid 圖表轉換為 Confluence ADF 格式。當需要在 Confluence 頁面中新增或更新 Mermaid 圖表時使用。支援 sequenceDiagram、flowchart、classDiagram 等所有 Mermaid 圖表類型。
allowed-tools:
  - Read
  - mcp__atlassian__getConfluencePage
  - mcp__atlassian__updateConfluencePage
  - mcp__atlassian__createConfluencePage
---

# Confluence Mermaid Skill

專門處理 Confluence 頁面中 Mermaid 圖表的新增與更新。使用 **Mermaid Diagrams for Confluence (Forge App)** 格式。

## 核心功能

1. **Mermaid 轉 ADF** - 將 Mermaid 程式碼轉換為 Confluence ADF extension 格式
2. **批次轉換** - 處理 Markdown 檔案中的多個 Mermaid code blocks
3. **寬度設定** - 支援 extension、wide、full-width 三種顯示寬度

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "在 Confluence 加入 Mermaid 圖表"
- "同步包含 Mermaid 的 Markdown 到 Confluence"
- "更新 Confluence 頁面的流程圖"
- "將這個 sequenceDiagram 加到 Confluence"
- "Confluence Mermaid 圖表渲染"

## ADF Extension 格式

### 正確格式 (Mermaid Diagrams Forge App)

```json
{
  "type": "extension",
  "attrs": {
    "extensionType": "com.atlassian.ecosystem",
    "extensionKey": "8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram",
    "text": "Mermaid diagram",
    "layout": "wide",
    "parameters": {
      "layout": "wide",
      "guestParams": {
        "input": "sequenceDiagram\n    participant A\n    participant B\n    A->>B: Hello",
        "url": ""
      }
    }
  }
}
```

### 欄位說明

| 欄位 | 值 | 說明 |
|------|-----|------|
| `type` | `"extension"` | ADF node 類型，必須是 extension |
| `extensionType` | `"com.atlassian.ecosystem"` | Forge App 固定值 |
| `extensionKey` | `"8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/..."` | Mermaid Diagrams App 的 UUID |
| `text` | `"Mermaid diagram"` | 顯示文字 |
| `layout` | `"wide"` 或 `"full-width"` | 顯示寬度 |
| `guestParams.input` | Mermaid 程式碼 | 使用 `\n` 作為換行符 |
| `guestParams.url` | `""` | 保持空字串 |

### Layout 選項

| Layout | 說明 | 建議使用情境 |
|--------|------|-------------|
| `extension` | 最窄，預設值 | 簡單小圖 |
| `wide` | 較寬 | **建議預設使用** - 大部分圖表 |
| `full-width` | 完整頁面寬度 | 非常複雜的大型圖表 |

## 錯誤格式 (請勿使用)

### 錯誤 1: bodiedExtension + Confluence Macro

```json
// ❌ 會顯示 "Error loading the extension!"
{
  "type": "bodiedExtension",
  "attrs": {
    "extensionType": "com.atlassian.confluence.macro.core",
    "extensionKey": "mermaid"
  }
}
```

### 錯誤 2: 純 Code Block

```json
// ❌ 只會顯示原始碼，不會渲染圖表
{
  "type": "codeBlock",
  "attrs": {
    "language": "mermaid"
  },
  "content": [
    {
      "type": "text",
      "text": "sequenceDiagram..."
    }
  ]
}
```

## 轉換流程

### 從 Markdown 轉換

1. **讀取 Markdown 檔案**
2. **識別 Mermaid code blocks**
   ```markdown
   ```mermaid
   sequenceDiagram
       A->>B: Hello
   ```
   ```
3. **轉換為 ADF extension 格式**
4. **更新 Confluence 頁面**

### Mermaid 程式碼處理

將 Mermaid 程式碼放入 `guestParams.input` 時：

- 保持原始格式
- 換行符轉為 `\n`
- 縮排空格保留
- 不需要額外跳脫

範例：

```
原始 Mermaid:
sequenceDiagram
    participant Client
    participant Server
    Client->>Server: Request
    Server-->>Client: Response

轉換後 input:
"sequenceDiagram\n    participant Client\n    participant Server\n    Client->>Server: Request\n    Server-->>Client: Response"
```

## 完整 ADF 範例

### sequenceDiagram

```json
{
  "type": "extension",
  "attrs": {
    "extensionType": "com.atlassian.ecosystem",
    "extensionKey": "8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram",
    "text": "Mermaid diagram",
    "layout": "wide",
    "parameters": {
      "layout": "wide",
      "guestParams": {
        "input": "sequenceDiagram\n    participant Client as 客戶端\n    participant API as API Gateway\n    participant Service as 服務\n    \n    Client->>API: 發送請求\n    API->>Service: 轉發請求\n    Service-->>API: 回傳結果\n    API-->>Client: 回傳回應",
        "url": ""
      }
    }
  }
}
```

### flowchart

```json
{
  "type": "extension",
  "attrs": {
    "extensionType": "com.atlassian.ecosystem",
    "extensionKey": "8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram",
    "text": "Mermaid diagram",
    "layout": "wide",
    "parameters": {
      "layout": "wide",
      "guestParams": {
        "input": "flowchart TD\n    A[開始] --> B{條件判斷}\n    B -->|是| C[執行動作]\n    B -->|否| D[其他動作]\n    C --> E[結束]\n    D --> E",
        "url": ""
      }
    }
  }
}
```

## 使用範例

### 範例 1: 單一圖表新增

```
User: "幫我在 Confluence 頁面加入這個流程圖:
flowchart LR
    A --> B --> C"

Claude: [啟用 confluence-mermaid Skill]

我將為您建立 Mermaid 圖表的 ADF 格式。

轉換結果:
{
  "type": "extension",
  "attrs": {
    "extensionType": "com.atlassian.ecosystem",
    "extensionKey": "8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram",
    "text": "Mermaid diagram",
    "layout": "wide",
    "parameters": {
      "layout": "wide",
      "guestParams": {
        "input": "flowchart LR\n    A --> B --> C",
        "url": ""
      }
    }
  }
}

請提供 Confluence 頁面 URL 或 Page ID，我將為您更新頁面。
```

### 範例 2: Markdown 同步到 Confluence

```
User: "將 docs/architecture.md 同步到 Confluence，裡面有 Mermaid 圖表"

Claude: [啟用 confluence-mermaid Skill]

1. 讀取 docs/architecture.md
2. 識別到 3 個 Mermaid code blocks
3. 將每個 Mermaid 轉換為 ADF extension 格式
4. 使用 updateConfluencePage API 更新頁面

轉換完成！所有 Mermaid 圖表都已使用 Forge App 格式，layout 設為 "wide"。
```

### 範例 3: 調整圖表寬度

```
User: "Confluence 上的 Mermaid 圖表太窄了"

Claude: [啟用 confluence-mermaid Skill]

我將讀取頁面並將所有 Mermaid 圖表的 layout 從 "extension" 改為 "wide"。

如果 "wide" 仍不夠寬，可以改為 "full-width" 使用完整頁面寬度。
```

## 注意事項

### 1. extensionKey 的重要性

`extensionKey` 是 Mermaid Diagrams Forge App 的唯一識別碼：

```
8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram
```

- 這是 **Mermaid Diagrams for Confluence** app 的固定值
- 如果 Confluence 站點安裝了不同的 Mermaid app，可能需要調整
- 可從現有正確渲染的 Mermaid 圖表中取得正確的 extensionKey

### 2. 中文支援

Mermaid 圖表支援中文，直接在 input 中使用即可：

```json
"input": "sequenceDiagram\n    participant 客戶\n    participant 伺服器\n    客戶->>伺服器: 發送請求"
```

### 3. 特殊字元處理

在 JSON 中需要跳脫的字元：
- `"` → `\"`
- `\` → `\\`
- 換行 → `\n`

### 4. 驗證圖表

更新頁面後：
1. 開啟 Confluence 頁面
2. 確認圖表正確渲染
3. 如果顯示錯誤，檢查 Mermaid 語法是否正確

## 快速參考

### 必要欄位

```json
{
  "type": "extension",
  "attrs": {
    "extensionType": "com.atlassian.ecosystem",
    "extensionKey": "8c5438cd-96d4-4c5b-a10b-dd06c1f5a7fc/f562d20f-bf6c-412c-affb-d78a16814320/static/mermaid-diagram",
    "layout": "wide",
    "parameters": {
      "layout": "wide",
      "guestParams": {
        "input": "YOUR_MERMAID_CODE_HERE",
        "url": ""
      }
    }
  }
}
```

### 常用 Layout

- `"wide"` - 建議預設值，適合大部分圖表
- `"full-width"` - 複雜大型圖表

## 總結

此 Skill 提供：
- 正確的 Mermaid Diagrams Forge App ADF 格式
- 避免常見錯誤格式（bodiedExtension、codeBlock）
- Layout 寬度選項說明
- 批次轉換 Markdown 中的 Mermaid 圖表
- 完整的範例和注意事項
