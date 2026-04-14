---
name: mermaid-diagram
description: 在 Markdown 檔案中撰寫 Mermaid 圖表時使用。確保 VS Code dark mode 下可讀性，包含白底 div 包裹和 theme 設定。適用於所有 Mermaid 圖表類型（sequenceDiagram、flowchart、classDiagram 等）。
allowed-tools:
  - Edit
  - Write
  - Read
---

# Mermaid Diagram Convention

在 Markdown 檔案中撰寫 Mermaid 圖表時，必須同時套用以下兩項以確保 VS Code dark mode 可讀性：

1. 用白底 `<div>` 包裹
2. 在 mermaid code block 第一行加 theme init

兩者缺一不可。

## 格式範本

```
<div style="background:#fff;padding:16px;border-radius:8px;">

```mermaid
%%{init: {'theme': 'default'}}%%
（Mermaid 內容）
```

</div>
```

## Theme 選擇順序

1. **首選**：`%%{init: {'theme': 'default'}}%%`
2. 備選（若 default 效果不佳時依序嘗試）：
   - `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#dce8f5', 'primaryTextColor': '#1a1a1a', 'primaryBorderColor': '#4a86c8', 'lineColor': '#555', 'secondaryColor': '#e6f3e6', 'tertiaryColor': '#fff5e6'}}}%%`
   - `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#c9d9f0', 'primaryTextColor': '#111', 'primaryBorderColor': '#3366aa', 'lineColor': '#444', 'secondaryColor': '#d4edda', 'tertiaryColor': '#fce4b8', 'noteBkgColor': '#fff3cd'}}}%%`
   - `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#d6e4f0', 'primaryTextColor': '#1a1a1a', 'primaryBorderColor': '#336699', 'lineColor': '#444', 'secondaryColor': '#d9ead3', 'tertiaryColor': '#fef2d4'}}}%%`
   - `%%{init: {'theme': 'forest'}}%%`

## 注意事項

- 適用於**所有** mermaid 圖表類型
- 白底 div 確保背景為白，default theme 確保節點顏色正常
