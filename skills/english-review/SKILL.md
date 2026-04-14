---
name: english-review
description: Collect English grammar/phrasing feedback Claude has given Eric during recent sessions and turn it into a daily practice exercise. Use this skill whenever Eric asks to review his English, practice his English, see today's English mistakes, do an English exercise, or wrap up his English practice for the day — even if he doesn't say the word "skill". Also use it when he says things like "let me practice", "quiz me on my English", "what did I get wrong today", or similar requests to learn from past feedback. Supports both static file generation and interactive quiz mode.
---

# English Review

Collects English feedback from Eric's recent Claude sessions and turns it into a practice exercise.

## Why this skill exists

Eric asked me to correct his English whenever he writes in English (see the **English Practice Convention** in `~/.claude/CLAUDE.md`). Those corrections are scattered across many sessions. Without consolidation, Eric never revisits them — so the mistakes repeat. This skill pulls them together so Eric can study and retain the corrections.

## When to trigger

Trigger on requests like:
- "review my English"
- "let me practice my English"
- "what English mistakes did I make today"
- "quiz me on my English"
- "end of day English review"
- Anything about consolidating or studying English feedback from past sessions

## Workflow

The skill has two modes, and the user chooses:

### Mode 1 — Generate static exercise file (default)

Use this when the user says "generate", "create the file", "make today's exercise", or doesn't specify.

1. Run the collector script to scan recent session transcripts and pull out English feedback blocks:

   ```bash
   python "C:\Users\eric.liao\.claude\skills\english-review\scripts\collect_feedback.py" --days 1
   ```

   Options:
   - `--days N` — how many past days to scan (default 1 = today only)
   - `--output PATH` — override output path (default `exercises/YYYY-MM-DD.md`)
   - `--project NAME` — filter by project directory name (default: all projects)

   The script writes a markdown file with:
   - Eric's original sentence (the mistake)
   - The corrections listed
   - A "cleaner rewrite" reference
   - A **Practice** section with blanks for Eric to fill in

2. Tell Eric where the file was written and offer to switch to interactive mode if he wants a quiz instead of self-study.

### Mode 2 — Interactive quiz

Use this when the user says "quiz me", "practice interactively", "walk me through", or asks to do the exercise live.

1. Run the collector script first to ensure today's exercise file exists (re-run it so data is fresh).
2. Read the generated markdown file.
3. Walk Eric through one item at a time:
   - Show him the original (incorrect) sentence
   - Ask him to rewrite it
   - When he replies, compare his answer against the stored correction and give feedback
   - Track a running score (correct / total)
4. At the end, summarize which patterns he got wrong most often and suggest 1-2 focus areas for tomorrow.

Keep the interactive pacing tight — one question, one answer, short feedback, move on. Don't lecture.

## Output format

The exercise file follows this structure. The script produces this shape; don't rewrite it unless the user asks.

```markdown
# English Review — 2026-04-13

Collected from N session(s). M feedback items.

## Item 1 — [short tag, e.g., "preposition"]

**Context (what you were asking):**
> {user's original message, truncated}

**Your sentence:**
> "{Eric's original English}"

**Corrections:**
- {point 1}
- {point 2}

**Cleaner rewrite:**
> "{suggested rewrite}"

**Practice — rewrite this correctly:**
> "{Eric's original English again}"

_Your answer:_ ___________________________

---

(repeat for each item)

## Summary

- Total items: N
- Most common pattern: {e.g., prepositions, articles, verb forms}
```

## Notes on the collector

- The script parses JSONL session files under `~/.claude/projects/*/`.
- It identifies assistant messages that contain an **"English feedback"** header (case-insensitive match on `english feedback`) and walks `parentUuid` back to find the user message that triggered the feedback.
- If no feedback is found in the scan window, the script exits cleanly with a message — in that case, tell Eric there's nothing to review today.

## Progressive disclosure

If the user asks how the script works internally, point them at `scripts/collect_feedback.py`. Don't dump the script contents into the conversation unless they ask.
