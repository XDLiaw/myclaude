---
name: prd-dev-readiness
description: PM self-check skill — analyse a PRD (a product REQUIREMENTS DOCUMENT, not a code PR — note the easy-to-confuse name) for gaps that would block or slow development, then emit a section-by-section HTML report with verbatim evidence, severity badges, owner tags, and paste-ready fix examples. Use when a PM wants to know "can I send this PRD to engineering now?" For reviewing code diffs use pr-review; for development plans use plan-review; can also be dispatched via review-router.
---

# PRD Dev-Readiness Check

PM 送 PRD 給 RD 前的自查工具。分析缺口 → 產出 HTML 報告，存本機。

## 觸發與輸入

- 使用者貼 Confluence URL → 用 `mcp__claude_ai_Atlassian__getConfluencePage` 抓內容
- 使用者貼純文字 → 直接分析
- 使用者貼附件/截圖 → OCR 後分析

## 輸出

HTML 檔案存到本機（**不發布 Artifacts / Cloud**），路徑：
`~/.obsidian/jamis/Projects/<project-name>/YYYY-MM-DD-prd-dev-readiness-<slug>.html`

完成後用 `open <path>` 讓用戶在瀏覽器看。

---

## 分析框架

### Phase 1：逐節掃描

按 PRD 章節順序掃，每節找三類問題：

| 類別 | 定義 | 解法 |
|---|---|---|
| **F 可行性** | 外部阻斷（API 無法存取、DB 連線未申請、外部系統未整合） | 找人確認事實 |
| **D 設計** | 內部邏輯矛盾（流程死鎖、狀態機缺失、定義相互矛盾） | 推理修邏輯 |
| **I 實作** | 缺具體值（算法未定、欄位名衝突、驗收條件用到未定義的值） | 補數值/定義 |

### Phase 2：嚴重性與 Owner 分類

**嚴重性（border 顏色）**
- 🔴 擋開發：不關閉 RD 無法估工時或無法動工
- 🟠 重要：開發中途會卡、但不擋啟動
- 🟡 補強：不補也能做，補了更好

**Owner（badge）**
- 🟢 你拍板：純業務規則，PM 一人決定
- 🟡 問 RD：技術事實，PM 需要去問 RD 再補進 PRD
- 🔵 跨部門：需要 DBA / 財務 / 維運等外部確認

### Phase 3：文字潤飾（8 個地雷）

每條 `.why` 和 `.fix` 說明都要過一遍：

1. **不是X而是Y** — 刪掉；直接說 Y
2. **過度鋪墊** — 刪掉開場白，直接說問題
3. **強迫結論** — 只說事實，不加「因此可以看出」
4. **小題大做** — 不要把一個小缺口升級成「整個系統風險」
5. **戲劇性過渡** — 不用「然而」「值得注意的是」這類詞
6. **有人說** — 不用「有觀點認為」；說清楚是 PRD 原文還是你的推論
7. **直白情緒** — 不用「非常嚴重」「完全不可接受」；用事實說話
8. **學術包裝** — 不用「基於上述分析」「綜合來看」；直接結論

說明標準：**像跟同事口頭解釋，不超過 3 句話，說清楚為什麼這是問題。**

---

## 每張缺口卡的結構

```
.item.b/.i/.m          ← 左 border 顏色 = 嚴重性
  .h = 🔴/🟠/🟡 標題  + .who owner badge
  .why = 白話說明（3 句以內，說清楚為什麼是問題）
  .ev = 證據區：
    .loc 標籤（UC-xx / §x / Q-x）+ 逐字 PRD 原文
    .gap = ⚠ 明確點出矛盾或缺口
  .fix = 修法區：
    .fl = 「怎麼補才算可以」
    說明（找誰、做什麼，1-2 句）
    .ex = 「可貼進 PRD 的寫法」（附範例句，可直接貼）
```

**所有 .why 說明只有 1-3 句，沒有標題，沒有鋪墊。**
**每張卡都要有 .ev 引文（逐字，不改寫），不能只憑印象說缺口。**
**80% 以上的卡要有 .fix .ex 範例句；純「事實確認類」（需要 RD 回覆才有內容）可只寫找誰問什麼。**

---

## 摘要框結構

報告最上方放一個摘要框，依序：

1. **判決句**（第一行，紅色粗體）：
   - `🔴 尚不具備送開發條件` — 有任何 🔴 擋開發缺口
   - `🟠 有條件送出` — 無 🔴 但有 🟠，需一起附上待確認清單
   - `🟢 可以送出` — 只有 🟡 以下

2. **計數列**：X 個缺口 + Y 個待確認，標色 badge

3. **送出前必做清單**（有序列表，最多 5 條，只列 🔴 擋開發的根因）

---

## HTML 模板（CSS + 結構）

```html
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRD 逐節體檢 — {PRD標題}</title>
<style>
  :root{
    --bg:#FBF0D9; --ink:#5F4B32; --accent:#B45309;
    --card:#FFF8EC; --card2:#F7ECD4; --border:#E3D2AC; --muted:#8A7355;
    --ev:#F2E5C6; --ev-bd:#D9C28C;
    --block:#B3261E; --imp:#BD5A0B; --minor:#9A7A12;
    --pm:#4F7A3A; --pm-bg:#E7F0DD; --rd:#9A6312; --rd-bg:#F5E7C8;
    --ext:#3F6E84; --ext-bg:#DFEDF2; --fix:#F0E6CF;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,
    "Songti TC","Noto Serif CJK TC",serif;
    line-height:1.64;font-size:16px;}
  .wrap{max-width:880px;margin:0 auto;padding:30px 20px 70px;}
  h1{font-size:1.7rem;margin:0 0 2px;}
  .sub{color:var(--muted);font-size:.9rem;margin:0 0 18px;}
  h2{font-size:1.18rem;margin:34px 0 10px;padding:6px 0 6px 11px;
     border-left:5px solid var(--accent);}

  /* 摘要框 */
  .ov{background:var(--card);border:1px solid var(--border);
      border-radius:10px;padding:14px 18px;margin:16px 0;}
  .verdict{font-weight:700;font-size:1.05rem;color:var(--block);margin-bottom:4px;}
  .verdict.ok{color:var(--pm);}
  .verdict.warn{color:var(--imp);}
  .counts{font-size:.92rem;margin:0 0 10px;}
  .cnt{font-size:.8rem;padding:1px 9px;border-radius:20px;margin-left:4px;}
  .c-b{background:#FBE2DD;color:var(--block);}
  .c-i{background:#FAE6CC;color:var(--imp);}
  .c-m{background:#F6EDC6;color:var(--minor);}
  .ov ol{margin:0;padding-left:20px;}
  .ov li{margin:4px 0;font-size:.94rem;}

  /* 目錄 */
  .toc{font-size:.9rem;margin:0 0 8px;color:var(--muted);}
  .toc a{color:var(--accent);margin-right:14px;}

  /* 缺口卡 */
  .item{background:var(--card);border:1px solid var(--border);
        border-left:5px solid var(--muted);border-radius:9px;
        padding:13px 16px;margin:11px 0;}
  .item.b{border-left-color:var(--block);}
  .item.i{border-left-color:var(--imp);}
  .item.m{border-left-color:var(--minor);}
  .h{font-weight:700;font-size:1rem;margin-bottom:6px;}
  .who{font-size:.74rem;padding:1px 8px;border-radius:20px;
       font-weight:400;white-space:nowrap;}
  .w-pm{background:var(--pm-bg);color:var(--pm);}
  .w-rd{background:var(--rd-bg);color:var(--rd);}
  .w-ext{background:var(--ext-bg);color:var(--ext);}
  .why{margin:5px 0;font-size:.93rem;}

  /* 證據區 */
  .ev{background:var(--ev);border-left:3px solid var(--accent);
      border-radius:4px;padding:7px 11px;margin:6px 0;
      font-size:.83rem;color:#5a482e;}
  .ev .row{margin:3px 0;line-height:1.5;}
  .ev .loc{display:inline-block;font-size:.71rem;background:#E5D4AC;
           color:#7a6230;padding:0 6px;border-radius:3px;
           margin-right:5px;font-weight:700;vertical-align:1px;}
  .ev .gap{margin-top:6px;padding-top:5px;
           border-top:1px dashed var(--ev-bd);
           font-weight:700;color:var(--accent);}

  /* 修法區 */
  .fix{background:var(--fix);border-radius:6px;
       padding:8px 11px;margin:7px 0 0;font-size:.92rem;}
  .fix .fl{font-size:.76rem;font-weight:700;color:var(--accent);
           margin-bottom:3px;letter-spacing:.5px;}
  .fix .ex{margin-top:6px;background:#fff;border-left:3px solid var(--pm);
           padding:5px 10px;font-size:.88rem;border-radius:3px;}
  .fix .ex b{color:var(--pm);font-size:.75rem;display:block;margin-bottom:1px;}

  /* 待確認表 */
  .tablewrap{overflow-x:auto;border:1px solid var(--border);
             border-radius:9px;margin:10px 0;}
  table{border-collapse:collapse;width:100%;min-width:560px;
        font-size:.87rem;background:var(--card);}
  th,td{text-align:left;padding:8px 11px;
        border-bottom:1px solid var(--border);vertical-align:top;}
  th{background:var(--card2);color:var(--accent);font-size:.8rem;}
  tr:last-child td{border-bottom:none;}
  .tag{font-size:.73rem;padding:1px 7px;border-radius:11px;white-space:nowrap;}
  .t-b{background:#FBE2DD;color:var(--block);}
  .t-i{background:#FAE6CC;color:var(--imp);}
  .t-m{background:#F6EDC6;color:var(--minor);}
</style>
</head>
<body>
<div class="wrap">

  <h1>PRD 逐節體檢報告</h1>
  <p class="sub">{PRD標題} {版本} · 逐節批註 · 每條附 PRD 逐字原文與補法範例</p>

  <!-- 摘要框 -->
  <div class="ov">
    <div class="verdict">🔴 尚不具備送開發條件</div>
    <div class="counts">
      {N} 個缺口 + {M} 個待確認：
      <span class="cnt c-b">🔴 擋開發 {n1}</span>
      <span class="cnt c-i">🟠 重要 {n2}</span>
      <span class="cnt c-m">🟡 補強 {n3}</span>
    </div>
    送 RD 前先處理這幾件：
    <ol>
      <!-- 只列 🔴 擋開發的根因，1-5 條 -->
    </ol>
    <div class="toc" style="margin-top:8px">
      找誰：
      <span class="who w-pm">🟢 你拍板</span>
      <span class="who w-rd">🟡 問 RD</span>
      <span class="who w-ext">🔵 跨部門</span>
    </div>
  </div>

  <!-- 目錄 -->
  <div class="toc">
    <!-- <a href="#sX">§X 節名</a> -->
  </div>

  <!-- 各節缺口卡 -->
  <!-- <h2 id="sX">§X 節名</h2> -->

  <!-- 缺口卡範本：
  <div class="item b">  ← b=🔴 i=🟠 m=🟡
    <div class="h">🔴 缺口標題 <span class="who w-rd">🟡 問 RD</span></div>
    <div class="why">白話說明，1-3 句，不超過，直接說問題。</div>
    <div class="ev">
      <div class="row"><span class="loc">UC-XX</span>「PRD 逐字原文」</div>
      <div class="gap">⚠ 矛盾/缺：明確點出問題所在。</div>
    </div>
    <div class="fix">
      <div class="fl">怎麼補才算可以</div>
      找誰、做什麼（1-2 句）。
      <div class="ex"><b>可貼進 PRD 的寫法</b>範例句，可直接複製貼入 PRD。</div>
    </div>
  </div>
  -->

  <!-- 待確認表（如有 §10 或 open questions） -->
  <!-- <h2 id="s-q">待確認盤點</h2>
  <div class="tablewrap">
  <table>
    <thead><tr><th>項目</th><th>在問什麼</th><th>找誰</th><th>急</th><th>相關</th></tr></thead>
    <tbody>
      <tr>
        <td>Q1</td><td>問題描述</td>
        <td><span class="tag w-rd">🟡 RD</span></td>
        <td><span class="tag t-b">高</span></td>
        <td>§X</td>
      </tr>
    </tbody>
  </table>
  </div> -->

</div>
</body>
</html>
```

---

## 執行步驟

1. **取得 PRD 內容**（URL fetch 或用戶貼文字）
2. **通讀全文，列出章節結構**（不要邊讀邊下結論）
3. **逐節找缺口**，每條記下：
   - 哪節哪條（UC-xx / §x / Qx）
   - 逐字原文（直接引用，不改寫）
   - 問題類型（F/D/I）
   - 嚴重性（🔴/🟠/🟡）
   - Owner（PM/RD/跨部門）
4. **過濾重複**：同一個根因只列一張卡，不要拆成多條
5. **過文字潤飾 checklist**（8 個地雷）
6. **組 HTML**：按 PRD 章節順序排卡，填摘要框
7. **存檔並 `open <path>`**

---

## 品質 Checklist（輸出前自查）

- [ ] 摘要框第一行是明確判決句（能/不能/有條件送出）
- [ ] 每張卡都有 .ev 逐字引文 + .loc 出處標籤
- [ ] 每個矛盾/缺口有 ⚠ 明確點出（不是暗示）
- [ ] 每張卡的 .why 不超過 3 句
- [ ] 8 個地雷都沒中
- [ ] 80% 以上的卡有 .fix .ex 範例句
- [ ] 待確認表有 owner 和優先序
- [ ] 判決句計數（🔴/🟠/🟡）與實際卡數一致
- [ ] 輸出到本機，沒有發布 cloud artifact
