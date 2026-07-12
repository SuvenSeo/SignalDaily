# Telegram Integration Guide

SignalDaily supports two Telegram modes.

## Mode 1: Manual alert

Use the Telegram-ready alert generated inside each daily brief.

Recommended flow:

1. Generate the daily brief.
2. Save it under `daily/YYYY-MM-DD.md`.
3. Copy the alert from the `GitHub-Ready Output` section.
4. Send it to your Telegram bot/channel manually.

## Mode 2: GitHub Actions reminder

The `Daily SignalDaily Reminder` workflow can send a simple Telegram reminder when these repository secrets are configured:

| Secret | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather. |
| `TELEGRAM_CHAT_ID` | User, group, or channel chat ID. |

The workflow does not generate the full AI report. It only reminds you to run the ChatGPT Agent and creates a GitHub issue for the day's brief.

## Why this design

This repo is currently optimized for no OpenAI API credits. The safe setup is:

```text
GitHub Actions -> daily reminder issue + optional Telegram ping
ChatGPT Agent -> research + write + commit report
SignalDaily repo -> permanent archive
```

## Future fully automated mode

When API credits are available, upgrade to:

```text
GitHub Actions -> Python collector -> OpenAI API -> Markdown report -> commit -> Telegram sendMessage
```

## Telegram formatting rules

- Prefer plain text for reliability.
- Keep alerts under 1,000 characters.
- Avoid MarkdownV2 unless all reserved characters are escaped.
- Do not include direct financial advice.
- Include the final GitHub file path.

## Bot safety

- Never commit `TELEGRAM_BOT_TOKEN` or chat IDs into the repo.
- Store tokens only as GitHub Actions secrets.
- Rotate the bot token if it is exposed.
- Do not allow untrusted users to trigger workflows that can access secrets.
