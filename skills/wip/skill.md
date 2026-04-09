---
name: wip
description: 查看未完成的工作進度紀錄，根據當前專案過濾，並提供 resume 原 session 或用接續 Prompt 開新對話兩種接續方式。支援跨日查找最近的 WIP 紀錄。
allowed-tools:
  - Bash
  - AskUserQuestion
---

# View & Resume WIP Sessions

查看並接續未完成的工作進度。

**效率要求：使用 bash script 一次完成檔案讀取和過濾，AI 只負責互動選擇。**

## Step 1: 一次取得所有 WIP 紀錄

用**單一 Bash 指令**呼叫 wip.sh 腳本，傳入當前 cwd 進行過濾：

```bash
bash ~/.claude/skills/wip/wip.sh "$(pwd)"
```

- 如果輸出為「目前沒有任何 WIP 紀錄」或「此專案...無未完成紀錄」→ 直接將訊息告知使用者，並詢問是否要查看全部專案紀錄。如果使用者同意，執行不帶參數的版本：

```bash
bash ~/.claude/skills/wip/wip.sh
```

- 如果有輸出紀錄 → 直接將結果呈現給使用者，每筆紀錄編號方便選擇。

## Step 2: 選擇紀錄並顯示接續資訊

詢問使用者要接續哪一筆（輸入編號）。

選定後，一次列出該筆紀錄的完整內容和兩種接續方式，讓使用者自行複製需要的部分：

```
### 完整紀錄
<摘要 + 待辦內容>

### Resume 指令（新終端機開啟）
claude --resume <session-id>

### Resume 指令（覆蓋當前 session）
/resume <session-id>

### 接續 Prompt
<去掉 blockquote `>` 前綴的 prompt 內容>
```
