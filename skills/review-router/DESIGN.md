# review-router — 設計文件

> 狀態：**待 Eric 審核**。核准後才依此建立 `SKILL.md`。
> 日期：2026-07-08

## 目標

把 Eric 自訂的四個 review 家族 skill 收斂成**單一前門**，並在 code lane 額外編排**內建 review 指令**當補充角度，解決兩個痛點並追求**最全面的 review 報告**：

1. **不知道選哪個** — 四個名字都像「review X」，手動時要記四個、易選錯。
2. **漏掉** — 只記得 `pr-review`，忘了有專門的 `test-effectiveness-auditor`，導致測試品質沒被好好審。
3. **求全面** — code lane 同時跑多個引擎（自訂 + 內建）再去重彙整，一次拿到最完整的發現。

## 非目標（明確不做）

- ❌ 不合併 `pr-review` 的 1000+ 行發佈引擎進來（會變怪物、難維護）。
- ❌ 不**修改**內建/plugin 指令的內容（改不了）；但**會用 Skill tool 呼叫**它們當額外審查角度。
- ❌ 不重用被佔用的名字 `review` / `code-review`（會撞名）→ 前門叫 `review-router`。
- ❌ 四個專家 skill 的內部邏輯**完全不改**（只改它們的 `description` 一行）。
- ❌ plan lane、prd lane 不做 fan-out（單一目標，沒必要）。
- ❌ **絕不自動套用會改 code 的指令**（`simplify`、`code-review --fix`）；一律 report-only。

## 架構：分類 → 條件式分派 → 彙整

`review-router` 本身很薄，只做三件事：

```
輸入 / 打 /review-router
   │
   ▼ ① 分類目標（不確定時只問一句）
   │
   ├─ code / MR / diff / commit ─▶ code lane（見下方 fan-out）
   ├─ 開發計畫 / 設計 ───────────▶ 委派 plan-review
   └─ PRD / Confluence 需求 ─────▶ 委派 prd-dev-readiness
```

### ① 分類訊號（預設規則）

| 判定為 | 訊號 |
|---|---|
| **code lane（publish 子模式）** | 輸入含 PR/MR URL、`owner/repo#N`，或使用者說「這個 MR / PR」 |
| **code lane（local 子模式）** | 指向 git diff / commit / branch / 「我的改動」「這段 code」，但**沒有** MR 識別碼 |
| **plan lane** | 指向計畫/設計文件，或剛產出一份開發計畫 |
| **prd lane** | 指向 PRD / Confluence 需求頁，或說「PRD / 需求文件」 |
| **不確定** | 只問**一個**問題，列出候選 lane 讓 Eric 選 |

### ② code lane 的 fan-out（Eric 的核心訴求落地處）

同一份 code diff 上，多個引擎各自從**互補角度**審查，再去重彙整成一份最全面的報告。

**引擎組合（全部 report-only，不改 code）：**

| 引擎 | 來源 | 角度 | 自動跑? |
|---|---|---|---|
| `pr-review` | 自訂 | bug / 邏輯 / 安全(diff) / 測試覆蓋 / spec 合規 | ✅ |
| `test-effectiveness-auditor` | 自訂 | 測試有沒有抓 bug 的能力 | ✅ |
| `code-review` | 內建 | 正確性 bug + reuse/簡化/效率/altitude 品質 | ✅（不加 `--fix`） |
| `security-review` | 內建 | 深度安全（pr-review 明文排除的 CVE/供應鏈那塊） | ✅ |
| `simplify` | 內建 | 品質簡化 | ⚠️ 選配，**會改 code**，不自動跑 |
| `review` / `code-review:code-review` | 內建/plugin | 通用 PR review | ❌ 與上面高度重疊，略過 |

**publish 子模式（有 MR）：**
1. 主線正常跑 `pr-review`（自帶 4 subagent 平行 + 發佈 sticky/inline 到 MR）。
2. 在同一份 diff 上跑 `test-effectiveness-auditor` + 內建 `code-review`（report-only）+ `security-review`。
3. 前門彙整一份合併報告。內建與測試有效性的發現**預設不發佈到 MR**（無發佈管線），只呈現給 Eric；只有 `pr-review` 的發現會進 MR。

**local 子模式（無 MR / pre-PR）：**
1. 前門**平行 dispatch 多個 subagent**：`pr-review`(local mode，回 JSON) + `test-effectiveness-auditor` + `code-review`(report-only) + `security-review`。
2. 全部回來後去重 + merge 成一份本機報告。

**安全紅線：** 所有引擎一律唯讀。`simplify` 與 `code-review --fix` 這種會改檔案的，**不列入自動 fan-out**；報告末端可提示「要套用簡化建議的話，手動跑 /simplify」。

**跨引擎去重：** 同一 `file:line` + 同類問題的發現合併成一條，標註「哪些引擎都指出」（多引擎同時抓到 = 可信度更高）。無法對齊行號的概念性發現各自保留。

### ③ 彙整輸出格式（code lane）

對話中呈現一份去重後的合併報告：

```
# review-router 合併報告

**引擎**：pr-review ✅ · test-effectiveness ✅ · code-review ✅ · security-review ✅
（哪個失敗要明講，不能靜默）

## 🔴 最該先處理（跨引擎去重後，依嚴重度排序）
- <finding> — 來源：pr-review + security-review（2 個引擎都指出）
- ...

## 分角度發現
### 🐞 Bug / 邏輯 / 正確性（pr-review, code-review）
### 🔒 安全（pr-review, security-review）
### 🧪 測試有效性（test-effectiveness-auditor）
### 🧹 品質 / 簡化（code-review）

## 一句話總評
<全部合起來，最該先動的是什麼>

## （選配）想套用簡化建議 → 手動跑 /simplify
```

publish 模式另附 `pr-review` 發佈到 MR 的 sticky 連結。

## 一併微調：四個專家 skill 的 description

只改 `description` 一行，讓**自動觸發**時邊界互斥、並把 Eric 導回前門。方向：

- `pr-review`：維持「PR/MR 程式碼 diff」，加註「若要連測試有效性一起審，用 review-router」。
- `test-effectiveness-auditor`：維持測試審核，加註「若要連 code bug 一起審，用 review-router」。
- `plan-review`：維持開發計畫/設計。
- `prd-dev-readiness`：維持 PRD（PM）；名字與 pr-review 相近，描述明確寫「這是需求文件 PRD，不是程式碼 PR」。

## 技術限制備忘

- Skill 在主線一次跑一個；要「真平行」得靠 dispatch subagent。故 local 子模式用兩個平行 subagent；publish 子模式因 `pr-review` 需在主線發佈，改為主線序列跑（pr-review 內部本來就平行）。
- `pr-review` 的 `mode: local` 本來就是設計給「被其他 skill 呼叫拿 JSON」用的，正好給前門使用。

## 決定紀錄（Eric 已確認）

1. ✅ publish 模式下，只有 `pr-review` 發佈到 MR；測試有效性與內建引擎的發現只給 Eric 看。
2. ✅ 分類不確定時「只問一句」而非猜。
3. ✅ 前門**納入內建 review 指令**（`code-review`、`security-review`），目標是最全面的報告；但一律 report-only，會改 code 的 `simplify` / `--fix` 不自動跑。

## 模式與參數（Eric 已確認）

- **預設 `full`**：跑 4 個引擎（pr-review / test-effectiveness / code-review / security-review）。
- **`quick`**：只跑 2 個自訂引擎（pr-review + test-effectiveness），省 token。
- `simplify`：**不自動跑**；報告末端提示「要套用簡化建議可手動跑 /simplify」。

呼叫範例：
- `/review-router <MR-URL>` → code lane, publish, full
- `/review-router quick` → code lane, local, quick
- `/review-router 這份計畫` → plan lane
