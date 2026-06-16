# Confluence 發布

對應主流程 **⑧ 發布到 Confluence** 與 **⑨ 收尾關聯**。使用 MCP Atlassian 工具發布。

## 目錄
- [發布資訊](#發布資訊)
- [建立 Release Note 頁面](#建立-release-note-頁面)
- [建立上版計畫子頁面](#建立上版計畫子頁面)
- [JIRA 單號連結格式（重要）](#jira-單號連結格式重要)
- [收尾關聯](#收尾關聯)
- [參考資源](#參考資源)

---

## 發布資訊

| 項目 | 值 |
|------|-----|
| Cloud ID | `f26ec960-9a0e-4396-966b-f9f61581d599` |
| Space ID | `23003199`（RD3 Space） |
| 父頁面 ID | **依專案規則文件**（`projects/{專案}.md`）；如 jkos-donation 為 `50364803` |

> Cloud ID 也可用 `getAccessibleAtlassianResources` 取得。父頁面 ID 一律以專案規則文件為準，不要寫死成其他專案的值。

## 建立 Release Note 頁面

```javascript
mcp__atlassian__createConfluencePage({
  cloudId: "f26ec960-9a0e-4396-966b-f9f61581d599",
  spaceId: "23003199",
  parentId: "{專案 release note 父頁 ID}",
  title: "{依專案標題格式}",
  body: "{release_note_content}",
  contentFormat: "markdown"   // 含 JIRA 連結時改用 html，見下方
})
```

## 建立上版計畫子頁面

```javascript
mcp__atlassian__createConfluencePage({
  cloudId: "f26ec960-9a0e-4396-966b-f9f61581d599",
  spaceId: "23003199",
  parentId: "{release_note_page_id}",  // 剛建立的 Release Note 頁面 ID
  title: "{依專案標題格式} 上版計畫",
  body: "{release_plan_content}",
  contentFormat: "markdown"
})
```

## JIRA 單號連結格式（重要）

Release Note 與上版計畫中**所有 JIRA 單號**（上版單、DB 異動票、開發項目、其他備註中的關聯單號等）一律使用 **inline smartlink**（行內卡片，顯示單號＋狀態膠囊），不要用純文字、也不要用顯示完整網址的普通超連結。

**做法**：以 `contentFormat: "html"` 發布/更新，JIRA 連結寫成：

```html
<a href="https://jkopay.atlassian.net/browse/{KEY}" data-card-appearance="inline">{KEY}</a>
```

**注意事項**：
- `contentFormat: "markdown"` **無法穩定指定 inline 行內卡片**：實測 `[KEY](url)` 單獨置於 cell 會變成未帶 appearance 的預設 smartlink、與文字並列（如標題內）則變成純超連結、裸 URL 則顯示整串網址。皆非想要的 inline 樣式 → 因此 JIRA 連結一律改用 HTML 格式明確指定 `data-card-appearance="inline"`。
- **非 JIRA 連結**（PRD、Design Review、其他 Confluence 頁面）維持一般超連結即可，不需 inline smartlink。
- 若需局部修改既有頁面，先用 `getConfluencePage`（contentFormat html）讀回完整 body，保留使用者既有調整，再整份重送。

## 收尾關聯

1. 上版單 ↔ DB 異動票 建立 `relates to` 關聯（`createIssueLink`，type `Relates`）。
2. 回填 Release Note 的「上版單」欄位為上版票（inline smartlink）。

---

## 參考資源

### Confluence 範本
- [ReleaseNote Template](https://jkopay.atlassian.net/wiki/spaces/Mobile/pages/806256819/ReleaseNote+Template) - Mobile 版本
- [上版計畫（Release Plan）範本](https://jkopay.atlassian.net/wiki/spaces/Engineering/pages/68845614/Release+Plan) - 完整版
- [RD3 - 上版計劃 Checklist](https://jkopay.atlassian.net/wiki/spaces/RD3/pages/976093224/RD3+-+Checklist) - 檢查清單

### RD3 Release Note 格式
參考 [NC] Release Note 系列文件的標準格式：預計上版日期、上版單（JIRA 連結）、Git（commit only）、Rollback Git（commit only）、DB 異動、UAPI 新增 routing、Vault 異動（檢查 `${XXXX}` 格式變數）、其他。
