# Global CLAUDE.md

This file provides global guidance to Claude Code across all projects.

## Always-On Rules

**CRITICAL:** Only perform actions that the user explicitly requests. Do NOT proactively execute additional steps (like committing, pushing, running tests, etc.) unless the user asks for them.

**IMPORTANT:** When responding to the user, always address them as "Eric" to maintain a personalized interaction.

**IMPORTANT — 輸出與回報：** 注意力是稀缺資源。多個 session 平行進行時，閱讀 AI 產出就是瓶頸。**先判斷完再交付，只給結論與待裁決事項**，不要把判斷工作丟回來。

寫法：

- **預設條列式**，避免多行描述段落。先給結論，再給必要細節。
- 一句一個概念。句子盡量不超過 25 字。
- 用主動語態、祈使句：寫「先執行 X」，不要寫「X 應該要被執行」。
- 同一件事全文用同一個詞，不要換詞。
- 刪掉鋪陳、客套、重複總結。不要隱喻、俚語、模糊修飾語（「基本上」、「相當地」）。
- 寧可少講：不清楚的地方會自己追問。

講多少：

- **對話回報固定三段**：`做了什麼`（≤3 行）／`需要你決定`／`檔案位置`。無待決事項就寫「無」。
- **「需要你決定」的判準**（只有符合才寫，其餘不寫）：
  1. 做了假設，猜錯要重做
  2. 下一步有副作用（DB、外部寫入、git 操作、刪檔）
  3. 發現與需求衝突，或既有 bug
  4. 有兩種做法、代價不同
- **過程不報**：搜尋、讀檔、重試、修 typo、測試通過 → 一律不寫。**只有失敗才寫**。
- **細節不刪、只搬家**：推導、比較、逐檔說明一律進檔案，console 只給**簡短摘要＋檔案位置**。
  **文件／報告／分析類產出一律用 HTML**（依下方 house style，不要用 Markdown 檔）；純程式碼變更直接改原始碼，讓人在 IDE 讀。
- **不複述已知**：不重述需求、不重述上一輪結論、結尾不加總結段。

**IMPORTANT — 報告分層（HTML／任何產出文件）：**

- **第一層＝預設可見，≤1 個螢幕（約 400 字）**：結論一句話／風險與待決（無就寫「無」）／影響範圍（哪個服務、哪張表、哪個 API）。
- **第二層＝`<details>` 收合，預設關閉**：推導過程、逐檔說明、log、程式碼、比較表。**收合在同一份 HTML**，不要另開檔案。
- **每個小節只回答一個問題**，答案直接寫在標題上。
- **每個發現標記 `要行動` / `僅供參考`**，第一層只放「要行動」。
- **禁止**：「背景說明」「需求回顧」章節；逐檔／逐函式清單（那是 git diff 的事）；大段 log／程式碼貼進第一層（改成 `檔案:行號` 或連結）；同一結論講三次；「我先做 A 再做 B」流水帳。
- **調查型報告例外**：細節一樣收合，但第一層**必須列出可自行查證的證據入口**——traceId、Kibana／Grafana 查詢連結、JIRA 單號、`檔案:行號`。證據入口屬第一層，不可收合。

**IMPORTANT — 文件修訂與驗收（改大份報告／設計文件時）：** 問題不是文件肥，是**無法只驗證改動**。每次修改都要附可逐項核對的憑證，不要讓人重讀全文。報告多為一次性（事故調查等），**不納入 git**，因此改用下列機制：

- **改檔前先備份**：把原檔複製到本次 session 的 scratchpad 目錄（不在專案內、不進版控）。
- **改完給 diff**：跑 `git diff --no-index <備份> <現檔>`（`--no-index` 不需要 repo）。回報 `改了 N 處` ＋ 逐處「章節／改前片段／改後片段」，每段片段 ≤1 行。原始 diff 等要求再給。
- **意見編號逐項回覆**：收到編號意見後，逐號回 `✅ 已改（說明）` 或 `⚠️ 未做（原因）`，附對應章節。驗收先看清單，有疑慮才看 diff。
- **章節搬移不給 diff**：改給「舊目錄 → 新目錄」兩欄對照表，並標註哪些是純搬移（內容未動）、哪些有改字。
- **不要在文件裡用 `<mark>` 標改動處**：會污染正式文件，下一輪還要清。
- **HTML 必須寫成 diff 友善格式**：每個區塊元素自己一行（`<p>`／`<li>`／`<tr>` 各一行），不要把整段擠成一行，否則 diff 整段變色等於沒用。
- 報告若放在專案 repo 內的資料夾，提醒把該資料夾加進 `.gitignore`。

**IMPORTANT — English Feedback (every message Eric writes in English):**
When Eric writes in English, ALWAYS review his grammar, word choice, and phrasing — even in casual/short messages. This is non-optional. Format:
1. Start with `### 📝 English Feedback` heading
2. Wrap all feedback in a **blockquote** (`>` prefix) for visual distinction
3. Each point: `> - "original" → "corrected" — explanation`
4. After all points, add: `> **Full corrected sentence:** "the entire sentence rewritten correctly"`
5. End blockquote, then a blank line, then `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` as separator, then a blank line, then main response

**IMPORTANT:** When executing any shell commands, always display the full command being executed in your response so the user can see and copy it.

**IMPORTANT — 絕不使用「TL;DR」：** 任何地方都不要出現 "TL;DR"——包含對話回覆，以及**產出的文件／報告（Markdown、HTML 等）**的標題、標籤或行內。若要在前面給快速摘要，改用「**懶人包**」當標題，或直接用一句白話重點帶出。

**IMPORTANT — 可自己查的先查再問：**
需要的資訊若能自行取得（現有程式碼、檔案、git 紀錄、Confluence／JIRA、網路搜尋），先查證再動手，**不要停下來問能自己找到的東西**。只有「查不到的內部決策／最新規格／個人偏好」才需要問。（此為讀取式調查，不違反上面「不主動執行額外動作」——那條指的是 commit／push／test 等有副作用的動作。）

**IMPORTANT — 貼 HTTP / log 紀錄到外部之前先查機敏資料並遮罩：**
只要把 HTTP request/response 或 log 內容貼到**會被他人或外部系統看到的地方**——JIRA 票券描述／comment、Slack、Confluence、對話回覆——一律先檢查是否含機敏資料，有就遮罩或整段刪除，不要整段複製貼上未經檢查的原始 dump。純粹寫進**不進 git 的本機報告**（debug 用途、只有自己看）可保留原值。

- **一律遮罩或整段移除**（不確定是否敏感，寧可遮）：
  - Header：`Authorization` / `Authenticate` / `Cookie` / `Set-Cookie` / 任何 `*Token*`、`*Key*`、`*Secret*` 命名的 header
  - Body 欄位：`password`、`token`、`secret`、`apiKey` 類欄位（`checksum` 只是防竄改雜湊值，非機敏資料，可保留）
  - 個資：身分證號、護照號碼、信用卡卡號、完整手機號／市話、完整地址、生日——只保留判斷情境所需的部分位數（例如身分證前 3 碼＋末 2 碼，中間用 `*` 補；系統本身回傳的遮罩格式如 `S22*****53` 可直接沿用，不用還原）
- **可保留**（非機敏、且是判斷根因所需）：URL path、業務欄位（單號、金額、狀態碼、時間戳）、traceId／correlationId、錯誤代碼/訊息、帳號識別碼（街口帳號、jkosId 等，視情境需要保留，但不可連同該帳號的身分證號／密碼一起完整曝光）

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

## 表格使用規則（文件、報告、JIRA 單一律適用）

**IMPORTANT：**表格是「對照矩陣」，不是「文件容器」。常見問題是某欄內容過長、擠成一團換行，整張表不可讀。產任何含表格的產出前先套下列規則：

- **只放可掃視的短值**：狀態、數字、代號、是/否、單號、`檔案:行號`、連結。
- **單格上限約 1 行（中文 ~25 字）**。超過就代表這格不該放在表格裡。
- **欄數上限 5**。優先砍掉「說明」「備註」「影響」這類天生會變長的欄。
- **一格超過 2 個要點 → 改 bullet**，不要用頓號／逗號串成一團。

**長內容往哪搬（不要塞回表格）**：
- 表格只留「編號 ＋ 一句話結論」，細節改成表格下方分節（`### A-1 xxx`，一節一事），表格那格放錨點連結。
- 三欄以上都是長文字 → 整張表廢掉，改成「每項一個小標 ＋ 段落」。

**HTML 報告**：
- `table-layout: fixed` ＋ 每欄明確 `width`，否則長欄會把其他欄壓扁。
- 短值欄 `white-space: nowrap`；只有長欄允許換行。
- 細節包 `<details>` 放在表格下方，不要塞進格子。
- 寬表格外層包 `overflow-x: auto`，不要為了塞進畫面而縮欄。

**JIRA**：
- Jira 表格更窄，長文字必爆版。長內容一律改 `h3` 分節 ＋ bullet，表格只留純對照矩陣（例：環境 × 狀態）。
- log／request/response 一律用 code block 或收合，不可放進表格格子。

## Design Review 文件（產 Confluence design 文件時一律照此規格）

**IMPORTANT：**產出 Design Review 文件時，一律照公司正式範本
[設計審查範本(Design Review Template)](https://jkopay.atlassian.net/wiki/spaces/Engineerin/pages/44335508/Design+Review+Template)（Engineering space, pageId `44335508`），**不要自己歸納既有文件的骨架、也不要自創章節**。

**文件命名**：`[{service name}]{requirement} ({需求名稱}) Design Review`
例：`[jkopay-app-svc] Referral Code (好友推薦碼) Design Review`

**章節骨架（固定，不可增刪層級）**：

```
1. 摘要（Abstract）
   1.1 需求背景 (PRD)        ← 附 PRD／JIRA 連結，簡述背景與技術 context
   1.2 名詞定義與統一命名      ← 條列術語，釐清同義詞一律用哪個稱呼
2. 系統架構
   2.1 資訊流中的物件         ← 依流程分 2.1.1 / 2.1.2…，各放流程圖；需含錯誤處理
   2.2 系統架構全圖
3. 實作細節
   3.1 溝通介面              ← 3.1.1 行動端 API / 3.1.2 網頁端 API / 3.1.3 Kafka…
   3.2 資料表及欄位的設計
       3.2.1 實體關係圖
       3.2.2 資料表架構       ← 每張表一個子節
4. 專案管理                  ← 表格：Team | Task | Assignee | Estimated time | Start Date
```

**填寫原則**：
- 範本要求、但本次需求沒有的章節，**保留標題並填「無」或「不適用」並簡述原因**，不要刪章節、也不要編造內容。
- 流程圖用 mermaid，**先用 `confluence-mermaid` skill 轉成 Confluence 格式**再放進頁面，不要貼原始碼。
- 建立／更新頁面時 `contentFormat` 用 **`html`**（markdown 會略過 macro）；寫完讀回確認圖表與 macro 正常。
- 放哪個 space／parent 依該產品線既有慣例（例如捐款掛在 RD3 的 `[NC] Design Review` 底下）。

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

**IMPORTANT — 純 rename 不必重跑完整測試：** 若改動純粹是重新命名（class/method/變數改名、搬移但邏輯不變），只要確保**編譯成功**即可，不需要為此額外重跑完整測試套件（省時間）。只有動到邏輯的改動才需要重跑測試。

## Branch / Worktree Workflow（開發前必做）

**CRITICAL — 進行任何開發（寫 code、改檔案）前，一律先確認 branch 狀態，不要直接在 `master`/`main` 上動手：**

1. **開發前先開專屬 branch**：動任何 code 之前，先檢查目前所在 branch。若還在 `master`/`main`，或沒有針對本次任務的專屬 branch，**先開一個針對性的新 branch** 再開始開發。branch 名稱要能反映任務主題。

2. **已在 feature branch 開發中／有未 commit 內容 → 考慮開 worktree**：若當前已處於某個 feature branch 且正在開發中，或工作區有尚未 commit 的變更，**不要**直接在原地切 branch（會污染或中斷現有工作）。改用 `git worktree` 開一個隔離工作區，且**一樣要在該 worktree 開新 branch**，於隔離環境進行新任務。

   - **固定放在 repo 的同層目錄**（repo 外、不要放 repo 內的 `.worktrees/`、`.claude/worktrees/` 等路徑——這些會造成每次位置不一致）：`<repo 所在目錄>/<worktree 名稱>`。
   - **命名規則依情境彈性決定**（例如 `<repo-name>-<JIRA單號>`、或遇中文路徑會導致工具問題時改全英文同層目錄如 `ebpp-worktrees/<topic>`），不強制單一格式，但同一個 repo 內**沿用該 repo 先前用過的慣例**（可用 `git worktree list` 確認既有 worktree 路徑模式）。
   - 不要再使用 `superpowers:using-git-worktrees` skill 的「智慧選目錄」邏輯（會導致 repo 內 `.worktrees/`／`.claude/worktrees/`／同層目錄三種並存、不一致）——直接依上述規則在同層目錄建立即可。

3. 不確定該開一般 branch 還是 worktree、或未 commit 的變更是否會被影響時，**先問 Eric 再動手**。

## Git Commit Convention

**IMPORTANT:** Do NOT automatically run `git commit` unless the user explicitly requests it.

**IMPORTANT:** Always run git operations as **standalone commands**. Never chain git commands with `cd` or other commands using `&&`. Always `cd` first, then run the git command separately.

Before creating a commit, always ask the user if there is a corresponding JIRA ticket. If there is, include the ticket number as a prefix, e.g. `[JKO-XXXXX] feat: ...`.
