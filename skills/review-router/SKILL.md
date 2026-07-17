---
name: review-router
description: Review 的單一前門。當使用者想 review / 審查 code、MR/PR、diff、commit、開發計畫、設計、或 PRD 需求文件時使用——尤其當他想要「最全面 / 徹底 / 多角度」的 review，或不確定該用哪個 review 工具時。本 skill 先分類要審的對象，再分派到對的專家（pr-review / test-effectiveness-auditor / plan-review / prd-dev-readiness），並在 code 情境下同時編排多個引擎（含內建 code-review、security-review）平行審查、去重、彙整成一份報告。當使用者只明確要單一面向（例如「只審測試」）時，讓對應的專家 skill 直接處理即可。
---

# Review Router

Review 家族的單一前門。目的：使用者不用記四個 review skill、也不會漏掉該搭配的引擎。本 skill 只做三件事——**分類 → 分派 → 彙整**——本身很薄，真正的審查交給專家引擎。

## 為什麼需要它

Eric 有多個 review 相關工具（自訂 + 內建），名字都像「review X」，實際使用時容易(1)不知道選哪個、(2)漏掉該一起跑的引擎（例如審 code 卻忘了專門的測試有效性審核）。前門用一致的入口解決這兩件事，並在 code 情境下追求「最全面的 report」。

## Step 1：分類要審的對象

從使用者輸入判斷落到哪個 lane。判斷不出來時**只問一個問題**列出候選 lane，不要亂猜。

| Lane | 訊號 |
|---|---|
| **code（publish 子模式）** | 輸入含 PR/MR URL、`owner/repo#N`，或說「這個 MR / PR / 這條 merge request」 |
| **code（local 子模式）** | 指向 git diff / commit / branch / 「我的改動」「這段 code」，但**沒有** MR 識別碼 |
| **plan** | 指向開發計畫 / 設計文件 / 實作方案，或使用者剛產出一份計畫要人審 |
| **prd** | 指向 PRD / Confluence 需求頁，或說「PRD / 需求文件 / 這份規格」（注意：是需求文件，不是程式碼 PR） |

分派：
- **plan lane** → 直接交給 `plan-review` skill 處理，不做 fan-out（單一目標）。
- **prd lane** → 直接交給 `prd-dev-readiness` skill 處理，不做 fan-out。
- **code lane** → 進入下方多引擎 fan-out。

## Step 2：code lane — 多引擎 fan-out

同一份 code diff 上，多個引擎各自從**互補角度**審查。先決定 **mode** 與 **子模式**：

- **mode**（預設 `full`）：
  - `full` — 跑 4 個引擎（最全面，token 較高）。
  - `quick` — 只跑 2 個自訂引擎（pr-review + test-effectiveness），省 token。使用者說 `quick` / 「快速」/「簡單看一下」時用。
- **子模式**：輸入有 MR/PR 識別碼 → `publish`；否則 → `local`。

### 引擎組合（全部 report-only，絕不改 code）

| 引擎 | 來源 | 角度 | full | quick |
|---|---|---|:--:|:--:|
| `pr-review` | 自訂 skill | bug / 邏輯 / 安全(diff) / 測試覆蓋 / spec 合規 | ✅ | ✅ |
| `test-effectiveness-auditor` | 自訂 skill | 測試有沒有抓 bug 的能力 | ✅ | ✅ |
| `code-review` | 內建指令 | 正確性 bug + reuse/簡化/效率/altitude 品質 | ✅ | — |
| `security-review` | 內建指令 | 深度安全（pr-review 明文排除的 CVE/供應鏈那塊） | ✅ | — |

**安全紅線（重要）：** 所有引擎一律唯讀。**絕不**自動跑會改檔案的 `simplify` 或 `code-review --fix`——review 報告全程不動使用者的 code，這符合 Eric CLAUDE.md 的「最小 diff、只做明確要求的事」。呼叫內建 `code-review` 時**不要**加 `--fix`；`simplify` 只在報告末端當提示。

### 怎麼跑（依子模式）

**local 子模式（無 MR / pre-PR）——真平行：**
在同一則訊息裡用多個 Agent tool 平行 dispatch，每個 subagent 跑一個引擎並回結構化發現：
- subagent A：呼叫 `pr-review` 的 **local mode**（`mode: local` + `base: <ref>`），回 findings JSON。
- subagent B：呼叫 `test-effectiveness-auditor`。
- （full 才有）subagent C：跑內建 `code-review`（report-only，不加 `--fix`）。
- （full 才有）subagent D：跑內建 `security-review`。

`pr-review` 的 `mode: local` 本來就是設計給「被其他 skill 呼叫拿 JSON」用的，正好給前門使用。

**publish 子模式（有 MR）——序列，因需在主線發佈：**
1. 主線正常跑 `pr-review`（自帶 4 subagent 平行 + 發佈 sticky/inline 到 MR）。
2. 在同一份 diff 上跑 `test-effectiveness-auditor`，full 再加 `code-review`(report-only) + `security-review`。
3. **只有 `pr-review` 的發現會進 MR**；其餘引擎的發現不發佈、只在對話裡彙整給 Eric（它們沒有發佈管線）。

任何引擎失敗都要在報告裡**明講**，不能靜默當作沒跑。

## Step 3：跨引擎去重 + 彙整（code lane）

多引擎必然重疊（例如安全問題 pr-review 與 security-review 都會報）。彙整規則：

- 同一 `file:line` + 同類問題 → 合併成**一條**，標註「哪些引擎都指出」。**被多個引擎同時抓到 = 可信度更高**，排序時往前。
- 無法對齊行號的概念性發現 → 各自保留，標來源。
- 依嚴重度排序（擋 merge 的 > 該修的 > 建議）。

### 報告格式

ALWAYS 用以下結構輸出到對話：

```
# review-router 合併報告

**引擎**：pr-review ✅ · test-effectiveness ✅ · code-review ✅ · security-review ✅
（失敗的引擎標 ❌ 並說明；quick 模式只列 2 個）

## 🔴 最該先處理（去重後，依嚴重度排序）
- <finding 一句話> — `file:line` — 來源：pr-review + security-review（2 引擎）
- ...

## 分角度發現
### 🐞 Bug / 邏輯 / 正確性（pr-review, code-review）
### 🔒 安全（pr-review, security-review）
### 🧪 測試有效性（test-effectiveness-auditor）
### 🧹 品質 / 簡化（code-review）

## 一句話總評
<全部合起來，最該先動的是什麼>

---
（選配）想套用簡化建議 → 手動跑 `/simplify`（會直接改 code，故不自動跑）
```

publish 模式在報告開頭附上 `pr-review` 發佈到 MR 的 sticky 連結。

## 呼叫範例

- `/review-router <MR-URL>` → code lane, publish, full
- `/review-router quick` → code lane, local, quick（審目前未 commit 的改動）
- `/review-router 這份計畫 docs/plan.md` → plan lane → plan-review
- `/review-router 這份 PRD <Confluence-URL>` → prd lane → prd-dev-readiness

## 邊界（不做什麼）

- 不修改任何專家 skill 或內建指令的內部邏輯，只編排它們。
- 不自動改 code（見安全紅線）。
- plan / prd lane 不做 fan-out（單一目標，交給對應專家即可）。
- 使用者若明確只要單一面向（「只審測試」「只做安全掃描」），可直接讓對應專家/指令處理，不必硬走前門。
