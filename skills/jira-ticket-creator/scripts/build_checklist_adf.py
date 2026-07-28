#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「資料庫異動檢查清單」JIRA comment 的 ADF JSON。

用途：DB 異動單建立後，把此腳本輸出的 ADF 以
      mcp__claude_ai_Atlassian__addCommentToJiraIssue（contentFormat: "adf"）貼上。

格式規格（已與使用者確立）：
- 問題維持一般字重；答案以「箭頭 → ＋ 粗體」與問題區隔。
- 已回答的核心答案：藍色 #0055CC；`【待填】`（尚未回答）：紅色 #AE2E24。
- 括號內的補充理由維持一般字重（不上色、不加粗）。
- 第 7 項（後續檢查）一律留空，不加箭頭、不代填（上線後才填）。
- 3.4 只填「跑多久」；「預計執行時間／是否避開尖峰」不代填、不標紅——
  取決於使用者實際排程，且低流量服務未必在意（留空即可）。

用法：
  python build_checklist_adf.py answers.json      # 從檔案讀
  echo '<json>' | python build_checklist_adf.py   # 從 stdin 讀

answers.json 結構（key 為題號字串；1.x–6.x 可填，7.x 忽略）：
  {
    "1.1": {"core": "新功能需求", "tail": "（JKO-31315 ...）"},
    "1.3": "否",                       # 字串 = 單一藍色核心答案
    "3.1": {"core": "【待填：影響筆數】", "pending": true},   # pending → 紅色
    "3.4": {"core": "數秒內", "tail": "（INSTANT）"},         # 只填跑多久，勿填避開尖峰
    "3.4b": {"segments": [["數秒內","c"], ["（INSTANT）","p"]]}  # 進階：自訂多段
  }
每個答案可用三種形式：
  - 字串                              → 單段藍色核心
  - {"core","tail","pending"}         → core 上色（pending 時紅色）＋ tail 一般字重
  - {"segments":[[text,style],...]}   → 自訂多段；style: "c"=上色 "p"=一般；配合 pending 決定藍/紅
未提供的 1.x–6.x 題 → 自動填紅色 `【待填】`。
"""
import json
import sys

BLUE = "#0055CC"
RED = "#AE2E24"

# (區塊標題, [(題號, 問題文字_不含尾端空白與箭頭), ...])
SECTIONS = [
    ("變更必要性", [
        ("1.1", "為什麼要進行這項資料庫異動?"),
        ("1.2", "為什麼沒有辦法使用系統後台進行資料庫異動?"),
        ("1.3", "之前是否曾經做過類似的變更，如果曾經做過，那麼什麼時候可以開始改用系統後台進行異動?"),
        ("1.4", "如果是因為系統問題造成的需求，我們是否知道系統的 Root Cause 是什麼? 以及是否有改善計畫?"),
        ("1.5", "之後是否有可能需要再次執行類似的 SQL? 如果有，那解決的計畫是?"),
    ]),
    ("程式碼審查 (Code Review):", [
        ("2.1", "SQL 是否有經過 Team Member Code Review? Review 人員是?"),
    ]),
    ("影響分析 (Impact Analysis):", [
        ("3.1", "SQL 可能影響的資料筆數?"),
        ("3.2", "SQL 是否有可能造成 Table lock?"),
        ("3.3", "SQL 變更是否對數據庫性能有負面影響，是否有需要跑執行計畫?"),
        ("3.4", "SQL 預計會跑多久? 預計執行的時間? 是否有避開尖峰時間?"),
        ("3.5", "SQL 預計執行期間是否與公司/行銷預計執行的活動有衝突? 是否鄰近假日或重要節日(e.g. 雙11)"),
    ]),
    ("測試執行 (Testing Execution):", [
        ("4.1", "SQL 是否有在測試環境進行過測試?"),
    ]),
    ("備案 (Contingency Planning):", [
        ("5.1", "資料是否有需要進行備份? 如果不需要的話，為什麼不需要?"),
        ("5.2", "如果執行結果不如預期，是否有 Rollback Plan?"),
    ]),
    ("文件記錄 (Documentation):", [
        ("6.1", "如果曾經做過類似的變更，是否有文件紀錄執行過程，以及清楚列出需注意的事項?"),
    ]),
    # 第 7 項一律留空
    ("後續檢查 (Post-deployment Review):", [
        ("7.1", "執行完畢後，執行結果是否符合預期"),
        ("7.2", "檢查是否有未預料的問題出現"),
    ]),
]


def _text(t, marks=None):
    n = {"type": "text", "text": t}
    if marks:
        n["marks"] = marks
    return n


def _colored(t, pending):
    return _text(t, [{"type": "strong"},
                     {"type": "textColor", "attrs": {"color": RED if pending else BLUE}}])


def _answer_segments(ans):
    """把一個答案值轉成 ADF text node 清單（不含前導箭頭）。"""
    pending = False
    if isinstance(ans, str):
        return [_colored(ans, False)]
    if isinstance(ans, dict):
        pending = bool(ans.get("pending"))
        if "segments" in ans:
            nodes = []
            for text, style in ans["segments"]:
                nodes.append(_colored(text, pending) if style == "c" else _text(text))
            return nodes
        nodes = [_colored(ans.get("core", ""), pending)]
        if ans.get("tail"):
            nodes.append(_text(ans["tail"]))
        return nodes
    return [_colored(str(ans), False)]


def build(answers):
    top = []
    for name, items in SECTIONS:
        is_last_section = name.startswith("後續檢查")
        subs = []
        for key, q in items:
            content = [_text(q)]
            if not is_last_section:  # 第 7 項不加箭頭、不代填
                ans = answers.get(key)
                if ans is None:
                    ans = {"core": "【待填】", "pending": True}
                content.append(_text(" → "))
                content.extend(_answer_segments(ans))
            subs.append({"type": "listItem",
                         "content": [{"type": "paragraph", "content": content}]})
        top.append({"type": "listItem", "content": [
            {"type": "paragraph", "content": [_text(name, [{"type": "strong"}])]},
            {"type": "orderedList", "content": subs},
        ]})
    return {"type": "doc", "version": 1, "content": [
        {"type": "heading", "attrs": {"level": 2}, "content": [_text("檢查清單")]},
        {"type": "orderedList", "content": top},
    ]}


def main():
    raw = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    answers = json.loads(raw) if raw.strip() else {}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(build(answers), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
