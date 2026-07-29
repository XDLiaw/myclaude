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

**IMPORTANT — 絕不使用「TL;DR」：** 任何地方都不要出現 "TL;DR"——包含對話回覆，以及**產出的文件／報告（Markdown、HTML 等）**的標題、標籤或行內。若要在前面給快速摘要，改用「**懶人包**」當標題，或直接用一句白話重點帶出。

## Infrastructure / Resources

**Kibana (log query)** — username for both environments: `eric.liao`. Passwords are NOT stored here; retrieve from password manager.
- SIT / UAT: https://log-kibana-gcp.jkopay.app
- PROD: https://log-kibana-gcp.jkopay.com

Older (deprecated, will be decommissioned — do NOT use):
- PROD (old): https://kibana.jkopay.com
- SIT / UAT (old): unknown / not recorded

**Reading logs via MCP (preferred over Playwright/Kibana web)** — global `elasticsearch` MCP servers in `~/.claude.json` (`mcpServers`) query the log clusters directly. Requires Docker running (uses `docker.elastic.co/mcp/elasticsearch`, one-shot `--rm` container per call).
- `elasticsearch` → SIT **and** UAT (one cluster `sit-operator-elastic`). Holds both K8s `rd3-{sit,uat}-*` data streams (**business logs are here**) and residual Swarm `swarm-{sit,uat}-*` data streams (metrics + RequestLoggingFilter only). Endpoint: `https://log-es-gcp.jkopay.app`. Auth: API key. NOTE: `rd3-*` has no `environment` field (use `kubernetes.*` labels); don't filter on `environment` or you'll silently drop business logs and see only Swarm metrics.
- `elasticsearch-prod` → PROD. Endpoint: `https://log-es-gcp.jkopay.com`. Auth: basic (username `eric.liao`).
- Secrets are NOT in config files — injected via env vars `${ES_SIT_API_KEY}` / `${ES_PROD_PASSWORD}` (set as Windows User env vars; changes require a full Claude Code restart).
- Logs are structured JSON: level field is `level` (not `log.level`); there is no single `message` field. Common fields: `service`, `environment`, `traceId`, `thread`.
- PROD account role is `editor`: `search` works, but `list_indices` / cluster monitor is denied (403) — query with index wildcards like `.ds-logs-*prod*<service>*` instead.

## GitLab 操作（改用 glab CLI，勿用 MCP）

**IMPORTANT:** 已移除 gitlab MCP（過去每個 session 常駐 ~1.5GB node），改用 glab CLI（單一執行檔、用完即退、零常駐）。做 GitLab 相關操作時一律優先用 glab，不要再嘗試 gitlab MCP。
- 執行檔：`C:\Users\eric.liao\AppData\Local\Programs\glab\glab.exe`（PATH 更新後可直接 `glab`；新 shell 若找不到就用完整路徑）
- 已認證 3 個 host（token 存於 `%LOCALAPPDATA%\glab-cli\config.yml`，明文，不在 public 的 `~/.claude` repo 內）：`gitlab.jkopay.app`、`gitlab.jkos.app`、`packages.jkos.com`
- **分工**：GitLab 平台操作（MR、issue、CI、review、diff）用 glab；本機 git（`commit`/`push`/`branch`）仍用一般 `git`。
- 在 repo 內 glab 會依 remote 自動選 host；跨 repo／非 repo 情境用 `glab api --hostname <host> <endpoint>`（例：`glab api --hostname gitlab.jkopay.app user`）。

## Code Style

**CRITICAL:** 編輯程式碼時，只修改與任務直接相關的行。**絕對不要**變動未涉及邏輯修改的行的縮排、換行、空白、import 排序或格式。目標是讓 `git diff` 保持最小化。

**IMPORTANT:** When accessing instance fields within a class, always use `this.` prefix for clarity.

## HTML Report / Document Style（產任何自包含 HTML 報告/計畫時沿用）

**IMPORTANT:** Eric 偏好一套固定的淺色 "house style"。**不要深色主題、不要漸層 / 彩色圓圈 / 重陰影**（他明確說過：深色偏暗、灰底不好看、漸層那種「太用力」不好看）。產 HTML 前直接套下列規格：

- **頁面底**：淺灰 `#f7f9fb`；內容用白色「紙張」`.wrap`（max-width ~960，`box-shadow:0 0 0 1px #e1e7ec`）
- **主色**：藍 `#2563eb`；文字 `#1f2933`、muted `#66757f`、線 `#e1e7ec`
- **h2**：藍色**底線**（`border-bottom:2px solid accent`），不要左色條
- **表格**：**每格都有格線**（`1px solid #e1e7ec`），表頭底 `#eef3f8`，偶數列 `#fafcfe`
- **行內 `code`**：`#eef1f4` 底、深色字；**程式碼區塊 `pre`：淺底 `#f6f8fa`＋邊框、深色字**（大區塊用深底會太黑，一律用淺底）
- **程式碼要做語法高亮**（尤其 YAML/config/程式碼），配色參考 **VS Code Light+**：註解綠 `#008000`、YAML key/property 藍 `#0451a5`、字串紅 `#a31515`、數字綠 `#098658`、布林/關鍵字藍 `#0000ff`。自包含 HTML 就用 token `<span>` 逐項上色（key/字串/數字/布林/註解都要上，不能只上註解）
- **callout / blockquote**：**左色條**＋淺色底（警告 `#fff7ed`/橘、危險 `#fef2f2`/紅、資訊 `#eff6ff`/藍）
- **badge**：**實心單色**、白字（不要漸層）
- **字型**：`"Segoe UI","PingFang TC","Microsoft JhengHei",system-ui`

認可的參考範本（可直接參考其 `<style>`）：
- `C:\Workspace\叫車\transporthub\documents\reports\20260706_JKO-31965_taxi-gps-zero\01_叫車GPS座標異常_調查報告.html`
- `C:\Workspace\繳費\jkopay-ebpp\docs\plan\tch-medical-efcs\07-database.html`

## Testing Conventions

**IMPORTANT — 每個測試方法都必須具備以下兩項：**

1. **`@DisplayName`**：用**中文**清楚描述測試情境與預期結果（例如 `"IC-001 查單 timeout → 回保險公司維護碼 2-IP-2999"`）。類別層級也應加 `@DisplayName` 說明受測對象。
2. **GIVEN / WHEN / THEN 區塊分隔**：測試 body 以 `// GIVEN:`、`// WHEN:`、`// THEN:` 三段註解分隔，每段註解要簡述該段在做什麼（不是只放空標籤）。三段之間空一行。
   - **GIVEN**：準備前置條件與 mock/stub
   - **WHEN**：執行受測行為（如 `assertThrows` 的呼叫）
   - **THEN**：斷言結果

範例：
```java
@Test
@DisplayName("IC-001 查單 timeout → 回保險公司維護碼 2-IP-2999")
void testQueryOrderTimeoutReturnsCompanyMaintenanceCode() {
    // GIVEN: 呼叫保險公司查單 API 發生連線逾時
    Call<...> call = this.callThrowing(new IOException("connect timed out"));
    Mockito.when(this.instantInsuranceApi.queryOrder(...)).thenReturn(call);

    // WHEN: 執行 IC-001 查單
    InsuranceServerException ex = Assertions.assertThrows(InsuranceServerException.class,
            () -> this.manager.queryOrder(...));

    // THEN: 視為上游不可控，回保險公司維護碼 2-IP-2999
    Assertions.assertEquals(ResponseCodeEnum.INS_COMPANY_UNKNOW_ERROR.getResult(), ex.getResult());
}
```

## Branch / Worktree Workflow（開發前必做）

**CRITICAL — 進行任何開發（寫 code、改檔案）前，一律先確認 branch 狀態，不要直接在 `master`/`main` 上動手：**

1. **開發前先開專屬 branch**：動任何 code 之前，先檢查目前所在 branch。若還在 `master`/`main`，或沒有針對本次任務的專屬 branch，**先開一個針對性的新 branch** 再開始開發。branch 名稱要能反映任務主題。

2. **已在 feature branch 開發中／有未 commit 內容 → 考慮開 worktree**：若當前已處於某個 feature branch 且正在開發中，或工作區有尚未 commit 的變更，**不要**直接在原地切 branch（會污染或中斷現有工作）。改用 `git worktree` 開一個隔離工作區，且**一樣要在該 worktree 開新 branch**，於隔離環境進行新任務。（可搭配 `superpowers:using-git-worktrees` skill）

3. 不確定該開一般 branch 還是 worktree、或未 commit 的變更是否會被影響時，**先問 Eric 再動手**。

## Git Commit Convention

**IMPORTANT:** Do NOT automatically run `git commit` unless the user explicitly requests it.

**IMPORTANT:** Always run git operations as **standalone commands**. Never chain git commands with `cd` or other commands using `&&`. Always `cd` first, then run the git command separately.

When creating git commits, DO NOT include:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"

Before creating a commit, always ask the user if there is a corresponding JIRA ticket. If there is, include the ticket number as a prefix, e.g. `[JKO-XXXXX] feat: ...`.
