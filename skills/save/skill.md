---
name: save
description: 儲存當前 session 的工作進度到每日 WIP 檔案。將對話摘要、待辦事項、JIRA 單號和接續 Prompt 記錄到 ~/.claude/wip/YYYY-MM-DD.md，方便隔天快速恢復工作。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - AskUserQuestion
---

# Save Session Progress

將當前對話的工作進度儲存到 WIP (Work In Progress) 檔案中。

**效率要求：最小化工具呼叫次數，所有機械步驟合併為一次 Bash 執行。AI 只專注在產生摘要內容。**

## Step 1: 一次取得所有 Session 資訊

用**單一 Bash 指令**同時取得 session ID、時間、cwd 資訊：

```bash
echo "=== SESSION ===" && for f in ~/.claude/sessions/*.json; do echo "---$(basename "$f" .json)---"; cat "$f"; echo ""; done 2>/dev/null && echo "=== TIME ===" && date '+%Y-%m-%d %H:%M' && echo "=== CWD ===" && pwd
```

從輸出中找到正確的 session：
1. 篩選 `cwd` 欄位與當前工作目錄匹配的 session JSON
2. 若有多筆匹配，選 `startedAt` 最大（最近啟動）的那筆
3. 取其 `sessionId`（找不到則記為「未知」）
4. 取得當前時間（YYYY-MM-DD HH:mm）
5. 取得 cwd，最後一段路徑作為 project-name

## Step 2: 產生完整 WIP 紀錄（一次完成）

**不要分步驟，在同一輪回應中一次完成以下所有工作：**

1. **JIRA 單號**：回顧對話上下文，如果有提到 JIRA 單號（如 `JKO-XXXXX`）就自動帶入。如果沒有，在呈現草稿時一併詢問。
2. **簡短標題**：一句話概括主要工作（10 字以內）
3. **摘要**：做了什麼、改了哪些檔案、解決什麼問題（3-5 句）
4. **待辦**：未完成項目，checkbox 格式
5. **接續 Prompt**：可直接貼到新 session 的 prompt，包含專案背景、已完成摘要、未完成待辦、JIRA 單號，語氣為指令式（brief 新同事接手），用 blockquote (`>`) 包裹

將以上內容組合成完整紀錄格式，**直接呈現給使用者確認**：

---

**以下是即將儲存的 WIP 紀錄，請確認是否正確（JIRA 單號如有誤請一併告知）：**

## [HH:mm] project-name — 簡短標題

- **Session ID:** `<session-id>`
- **JIRA:** `<jira-ticket>`（或「無」）
- **專案路徑:** `<cwd>`
- **時間:** YYYY-MM-DD HH:mm

### 摘要
<摘要內容>

### 待辦
- [ ] <待辦項目 1>
- [ ] <待辦項目 2>

### 接續 Prompt
> <接續 prompt 內容>

---

詢問使用者：「以上內容是否正確？可以告訴我要修改的部分，或回覆『OK』確認儲存。」

如果使用者要求修改，調整後再次呈現確認，直到使用者確認 OK。

## Step 3: 儲存到 WIP 檔案

使用者確認後，用**單一 Bash 指令**完成目錄建立和檔案寫入：

```bash
mkdir -p ~/.claude/wip && FILE=~/.claude/wip/YYYY-MM-DD.md && if [ ! -f "$FILE" ]; then echo "# WIP — YYYY-MM-DD" > "$FILE" && echo "" >> "$FILE"; fi && cat >> "$FILE" << 'WIPEOF'

<確認後的完整紀錄內容>
WIPEOF
```

儲存完成後告知：「已儲存到 `~/.claude/wip/YYYY-MM-DD.md`」
