# SignalDaily Operations Manual

This repo currently uses the ChatGPT Agent-based workflow. It does not require OpenAI API credits.

## Current operating choice: Option B

Use one scheduled ChatGPT Agent run per day for the full report. Use three lightweight/manual updates only when needed.

```text
06:00 — Full SignalDaily daily brief, agent scheduled
12:00 — Lightweight midday pulse, manual/on-demand if needed
18:00 — Lightweight evening pulse, manual/on-demand if needed
00:00 — Lightweight overnight/global watch, manual/on-demand if needed
```

This keeps monthly scheduled agent usage low while still giving a path for extra updates when important things happen.

## Daily workflow

1. Let the SignalDaily ChatGPT Agent run at the scheduled time.
2. The agent should research and generate a GitHub-ready Markdown report.
3. The agent should attempt to save the report to this repo if GitHub write actions are available.
4. If automatic GitHub writing is not available, copy the generated Markdown manually into:

```text
daily/YYYY-MM-DD.md
```

5. Commit with:

```text
daily: add SignalDaily brief for YYYY-MM-DD
```

6. Send the Telegram-ready alert manually, or use it in your Telegram bot/channel.

## Daily agent prompt

Use this as the scheduled task prompt:

```text
Run today's SignalDaily brief. Research current AI, technology, coding tools, Sri Lanka/CSE/economy, global markets, and opportunity signals. Generate a GitHub-ready Markdown report using the SignalDaily format.

After generating the report, attempt to update the GitHub repository SuvenSeo/SignalDaily by creating or updating daily/YYYY-MM-DD.md with the full report. Use commit message: daily: add SignalDaily brief for YYYY-MM-DD.

If you cannot write to GitHub directly, clearly say that and provide the full Markdown report, suggested file path, commit message, and Telegram-ready alert message.
```

## Lightweight update workflow

Use lightweight updates only when needed. Save them under:

```text
updates/YYYY-MM-DD-HHMM.md
```

Recommended update types:

```text
12:00 — Midday pulse
18:00 — Evening pulse
00:00 — Overnight/global watch
```

Use this prompt:

```text
Create a lightweight SignalDaily update for YYYY-MM-DD HH:MM. Cover only major new developments since the last brief. Keep it short, sourced, and GitHub-ready. If GitHub writing is available, save it to updates/YYYY-MM-DD-HHMM.md. If not, provide the Markdown, file path, commit message, and Telegram-ready alert.
```

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

Recommended schedule for full-month stability:

```text
Daily at 6:00 AM Sri Lanka time
```

Use the 12:00, 18:00, and 00:00 updates manually or on demand unless the plan has enough scheduled agent allowance.

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

## Automatic GitHub update test

To test whether the SignalDaily Agent can write to GitHub, ask it:

```text
Create a test file in SuvenSeo/SignalDaily at test/agent-github-write-test.md with one sentence saying the GitHub write test worked. Commit it with message: test: verify agent GitHub write access.
```

If the file appears in the repo, the agent has a working write path. If it only gives you Markdown or asks for approval, automatic unattended repo writing is not fully enabled.

## Upgrade path

When OpenAI API credits become available, this repo can be upgraded to:

```text
GitHub Actions -> Python collector -> OpenAI API -> Markdown report -> commit -> Telegram alert
```

Until then, keep this as a clean agent-driven intelligence archive.
