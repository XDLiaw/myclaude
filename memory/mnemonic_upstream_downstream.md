---
name: mnemonic-upstream-downstream
description: Eric 記 upstream/downstream 的口訣「拿人手短」；解釋呼叫鏈方向時用這套跟他對齊
metadata:
  type: user
---

Eric 常忘記 upstream/downstream，偏好用他自己的口訣理解：**「拿人手短，自然矮一截，所以在下面」**。

判定標準（跟資料流向無關，資料是雙向的所以流向是爛比喻）：
- **主動發起呼叫的一方 = downstream（下游）**＝有求於人、拿人手短、矮一截、在下面
- **被呼叫、被依賴的一方 = upstream（上游）**＝被求、站得高、在上面
- upstream/downstream 是**每一次呼叫各自認定**，不是固定貼在服務上的 label；發起方換人，上下游就反過來。

雙向呼叫的例子（保險 ↔ onlinepay）：
- A 主動打 B 下單／查詢 → A 是下游、B 上游
- B 主動打 A 的 callback API → B 下游、A 上游（同兩個服務，發起方換人就反過來）

**How to apply:** 之後跟 Eric 解釋呼叫鏈方向（尤其 callback 這種雙向流程）時，直接用「拿人手短 → 下游」這套術語對齊，不用每次重新推導。此為通用概念，放全域跨專案適用。
