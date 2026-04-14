#!/bin/bash
# Remind Claude to provide English feedback when Eric writes primarily in English
# Triggered on UserPromptSubmit

INPUT=$(cat)

# Extract "input" field without jq — grab value between quotes after "input":
USER_MSG=$(echo "$INPUT" | sed -n 's/.*"prompt"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/p')

[ -z "$USER_MSG" ] && exit 0

# Count English letters vs total non-whitespace characters
TOTAL=$(echo "$USER_MSG" | tr -d '[:space:]' | wc -c)
ENGLISH=$(echo "$USER_MSG" | tr -cd 'a-zA-Z' | wc -c)

[ "$TOTAL" -eq 0 ] && exit 0

# Only trigger when English characters make up >60% of the message
RATIO=$((ENGLISH * 100 / TOTAL))
if [ "$RATIO" -gt 60 ]; then
  cat <<'EOF'
⚠️ ENGLISH DETECTED — You MUST provide English feedback BEFORE your main response.
Format rules:
1. Start with heading: ### 📝 English Feedback
2. Wrap ALL feedback lines in a blockquote (prefix every line with >)
3. Each point: > - "original" → "corrected" — explanation
4. End the blockquote, then --- separator, then your main response
5. Even casual/short messages need review. Do NOT skip this.

Example:
### 📝 English Feedback
> - "do i miss to commit" → "did I miss committing" — use gerund after "miss", past tense for completed action

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(main response here)
EOF
fi
