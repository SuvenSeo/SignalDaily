# Telegram Alert Template

Use this template for short Telegram bot/channel updates.

```text
SignalDaily — YYYY-MM-DD

Top signals:
1. Signal one in one short line.
2. Signal two in one short line.
3. Signal three in one short line.
4. Signal four in one short line.
5. Signal five in one short line.

Best opportunity:
- One practical build/research idea.

Full report:
daily/YYYY-MM-DD.md
```

## Rules

- Keep the alert under 1,000 characters unless the user asks for detail.
- Do not include long analysis.
- Include only the top signals, best opportunity, and file path.
- Use direct, clean wording.
- Do not include financial advice.
- Avoid MarkdownV2 special formatting unless escaped correctly.
- If using Telegram Bot API `sendMessage`, prefer plain text unless formatting is required.
