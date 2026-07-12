# SignalDaily Operations Manual

This repo currently uses the ChatGPT Agent-based workflow. It does not require OpenAI API credits.

## Daily workflow

1. Open the SignalDaily ChatGPT Agent.
2. Run this prompt:

```text
Run today's SignalDaily brief. Make it GitHub-ready for SuvenSeo/SignalDaily. Include the suggested file path, commit message, and Telegram-ready alert message.
```

3. Review the generated Markdown.
4. Create a new file in this repo under:

```text
daily/YYYY-MM-DD.md
```

5. Paste the Markdown.
6. Commit with:

```text
daily: add SignalDaily brief for YYYY-MM-DD
```

7. Send the Telegram-ready alert manually, or use it in your Telegram bot/channel.

## Weekly workflow

At the end of the week, run:

```text
Create this week's SignalDaily recap. Summarize the biggest AI, tech, coding, Sri Lanka/CSE, global market, and opportunity trends from the daily reports. Save-path suggestion must be weekly/YYYY-WW.md.
```

Save it under:

```text
weekly/YYYY-WW.md
```

## Monthly workflow

At the end of the month, run:

```text
Create a monthly SignalDaily review. Identify recurring themes, major shifts, missed signals, strong opportunities, and topics to monitor next month. Save-path suggestion must be monthly/YYYY-MM.md.
```

Save it under:

```text
monthly/YYYY-MM.md
```

## Agent schedule

Recommended schedule:

```text
Daily at 6:00 AM Sri Lanka time
```

Alternative:

```text
Daily at 9:00 AM Sri Lanka time
```

Use 6:00 AM if you want an early briefing before the day starts. Use 9:00 AM if you want more sources to update first.

## Telegram alert workflow

The agent should generate a short alert under 1,000 characters using `templates/telegram-alert-template.md`.

Example:

```text
SignalDaily — YYYY-MM-DD

Top signals:
1. ...
2. ...
3. ...
4. ...
5. ...

Full report:
daily/YYYY-MM-DD.md
```

## Upgrade path

When OpenAI API credits become available, this repo can be upgraded to:

```text
GitHub Actions -> Python collector -> OpenAI API -> Markdown report -> commit -> Telegram alert
```

Until then, keep this as a clean agent-driven intelligence archive.
