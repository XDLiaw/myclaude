# Global CLAUDE.md

This file provides global guidance to Claude Code across all projects.

## Git Commit Convention

**IMPORTANT:** Do NOT automatically run `git commit` unless the user explicitly requests it. Only commit when the user says "commit" or similar explicit instructions.

**IMPORTANT:** Always run git operations as **standalone commands**. Never chain git commands with `cd` or other commands using `&&`. Always `cd` first, then run the git command separately. This applies to all git operations including `git push`, `git commit`, `git pull`, etc.

✅ Correct:
```bash
cd /path/to/project
git push origin main
```

❌ Wrong:
```bash
cd /path/to/project && git push origin main
```

**IMPORTANT:** When creating git commits, DO NOT include the following in commit messages:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"

Keep commit messages clean and focused on the actual changes.

**IMPORTANT:** Before creating a commit, always ask the user if there is a corresponding JIRA ticket. If there is, include the ticket number as a prefix in the commit message, e.g. `[JKO-XXXXX] feat: ...`.

## Code Style Guidelines

### Minimal Diff Convention
**CRITICAL:** 編輯程式碼時，只修改與任務直接相關的行。**絕對不要**變動未涉及邏輯修改的行的縮排、換行、空白、import 排序或格式。即使現有格式不符合你偏好的風格，也不要順手調整。

目標是讓 `git diff` 保持最小化，只呈現實質變更，避免 noise。

常見違規情境：
- ❌ 重新排列 import 順序
- ❌ 調整未修改行的縮排或空行
- ❌ 將單行拆成多行（或反之），但該行邏輯未變
- ❌ 移除或新增與任務無關的尾端空白

### Field Access Convention
**IMPORTANT:** When accessing instance fields within a class, always use `this.` prefix for clarity.

✅ Good:
```java
return this.userRepository.findById(id);
```

❌ Bad:
```java
return userRepository.findById(id);  // Missing this.
```

## Command Output Convention

**IMPORTANT:** When executing any shell commands, always display the full command being executed in your response so the user can see and copy it.

## Response Convention

**IMPORTANT:** When responding to the user, always address them as "Eric" to maintain a personalized interaction.

## Mermaid Diagram Convention

**IMPORTANT:** When writing Mermaid diagrams in Markdown files, must apply BOTH of the following to ensure readability in VS Code dark mode:

1. Wrap with white background `<div>`: `<div style="background:#fff;padding:16px;border-radius:8px;">`
2. Add `%%{init: {'theme': 'default'}}%%` as the **first line** inside the mermaid code block

兩者缺一不可，白底 div 確保背景為白，default theme 確保節點顏色正常。

Format:
1. Opening tag: `<div style="background:#fff;padding:16px;border-radius:8px;">`
2. A blank line
3. The mermaid code block (triple backticks with mermaid language tag)
4. First line: `%%{init: {'theme': 'default'}}%%`
5. Mermaid content
6. A blank line
7. Closing tag: `</div>`

Rules:
- **首選**：`%%{init: {'theme': 'default'}}%%`
- **備選方案**（若 default 效果不佳時依序嘗試）：
  1. `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#dce8f5', 'primaryTextColor': '#1a1a1a', 'primaryBorderColor': '#4a86c8', 'lineColor': '#555', 'secondaryColor': '#e6f3e6', 'tertiaryColor': '#fff5e6'}}}%%`
  2. `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#c9d9f0', 'primaryTextColor': '#111', 'primaryBorderColor': '#3366aa', 'lineColor': '#444', 'secondaryColor': '#d4edda', 'tertiaryColor': '#fce4b8', 'noteBkgColor': '#fff3cd'}}}%%`
  3. `%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#d6e4f0', 'primaryTextColor': '#1a1a1a', 'primaryBorderColor': '#336699', 'lineColor': '#444', 'secondaryColor': '#d9ead3', 'tertiaryColor': '#fef2d4'}}}%%`
  4. `%%{init: {'theme': 'forest'}}%%`
- This applies to ALL mermaid diagram types (sequenceDiagram, flowchart, classDiagram, etc.)

## Plan Review Convention

**IMPORTANT:** 產出任何開發計畫後，必須自動執行以下四步驟深度 Review：

1. **核心與架構驗證**：用第一性原理檢驗計畫的核心邏輯是否穩固，並用批判性思維找出潛在盲點。
2. **設計精簡（奧卡姆剃刀）**：明確指出計畫中是否有過度設計（Over-engineering）或可被移除的多餘元素。
3. **場景窮舉（MECE）**：檢視現有的測試案例，評估其是否達到 MECE（相互獨立、完全窮舉）的標準。
4. **深度場景探索**：切換思維，利用不同角色代入（新手、極端依賴者、惡意操作者），針對「異常路徑（Unhappy Path）」、「網路/硬體極限狀態」與「邊界值」，補充 5-10 個計畫中遺漏的邊緣測試場景。

## General Guidelines

- Focus on writing clean, maintainable code
- Follow project-specific conventions when they exist
- Prioritize simplicity over complexity
- **CRITICAL:** Only perform actions that the user explicitly requests. Do NOT proactively execute additional steps (like committing, pushing, running tests, etc.) unless the user asks for them.
