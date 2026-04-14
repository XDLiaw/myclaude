---
name: jira-sprint
description: 查詢 JIRA sprint 相關資訊時使用。包含正確查詢「下個 sprint」的步驟、sprint 命名規則解讀、避免常見錯誤（如直接用 futureSprints 撈全部）。
allowed-tools:
  - WebFetch
  - Bash
---

# JIRA Sprint Convention

Atlassian Cloud ID: `f26ec960-9a0e-4396-966b-f9f61581d599` (jkopay.atlassian.net)

## 查詢「下個 Sprint」的正確步驟

1. 先查當前 active sprint（`sprint in openSprints()`），取得 sprint 名稱與所屬 board
2. 再查 future sprints（`sprint in futureSprints()`），找同 board 下**最近的一個** future sprint
3. 用該 sprint ID 篩選 `assignee = currentUser()` 的票

## Sprint 命名規則

以支付應用 board 為例：

- 格式：`支付應用 (日期範圍) {年}Q{季}C{Cycle}`
- 例如：`支付應用 (4/6-4/10) 2026Q2C1`
- **每個 Cycle 包含多個週 sprint**，每週一個 sprint（不是 C1 → C2 遞增代表下個 sprint）

## 常見錯誤

- ❌ 直接用 `futureSprints()` 撈全部 — 會包含其他 board 和遠期 backlog 的票
- ✅ 必須鎖定**同 board 的下一個 future sprint** 才是真正的「下個 sprint」
