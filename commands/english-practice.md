---
description: Interactive English practice — quizzes Eric on feedback collected from recent sessions
---

Invoke the `english-review` skill in **interactive quiz mode**.

Steps:
1. Run the collector script to refresh today's exercise file:
   `python "C:\Users\eric.liao\.claude\skills\english-review\scripts\collect_feedback.py" --days 1`
2. Read the generated file at `C:\Users\eric.liao\.claude\skills\english-review\exercises\<today>.md`.
3. Walk Eric through each item one at a time:
   - Show the original (incorrect) sentence only — do **not** reveal the corrections yet.
   - Ask him to rewrite it.
   - When he replies, compare against the stored corrections and give concise feedback (right / partially right / wrong, plus the key point he missed).
   - Keep a running score.
4. At the end, summarize:
   - Final score (correct / total)
   - Top 1-2 recurring patterns he should focus on tomorrow

Rules:
- One question at a time. Don't dump the whole list.
- If there are no items in the file, tell Eric there's nothing to practice today and stop.
- Arguments (if provided): `$ARGUMENTS` — treat as overrides, e.g., `--days 3` to widen the scan window.
