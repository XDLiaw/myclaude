# Global CLAUDE.md

This file provides global guidance to Claude Code across all projects.

## Always-On Rules

**CRITICAL:** Only perform actions that the user explicitly requests. Do NOT proactively execute additional steps (like committing, pushing, running tests, etc.) unless the user asks for them.

**IMPORTANT:** When responding to the user, always address them as "Eric" to maintain a personalized interaction.

**IMPORTANT — English Feedback (every message Eric writes in English):**
When Eric writes in English, ALWAYS review his grammar, word choice, and phrasing — even in casual/short messages. This is non-optional. Format:
1. Start with `### 📝 English Feedback` heading
2. Wrap all feedback in a **blockquote** (`>` prefix) for visual distinction
3. Each point: `> - "original" → "corrected" — explanation`
4. After all points, add: `> **Full corrected sentence:** "the entire sentence rewritten correctly"`
5. End blockquote, then a blank line, then `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` as separator, then a blank line, then main response

**IMPORTANT:** When executing any shell commands, always display the full command being executed in your response so the user can see and copy it.

## Code Style

**CRITICAL:** 編輯程式碼時，只修改與任務直接相關的行。**絕對不要**變動未涉及邏輯修改的行的縮排、換行、空白、import 排序或格式。目標是讓 `git diff` 保持最小化。

**IMPORTANT:** When accessing instance fields within a class, always use `this.` prefix for clarity.

## Git Commit Convention

**IMPORTANT:** Do NOT automatically run `git commit` unless the user explicitly requests it.

**IMPORTANT:** Always run git operations as **standalone commands**. Never chain git commands with `cd` or other commands using `&&`. Always `cd` first, then run the git command separately.

When creating git commits, DO NOT include:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"

Before creating a commit, always ask the user if there is a corresponding JIRA ticket. If there is, include the ticket number as a prefix, e.g. `[JKO-XXXXX] feat: ...`.
