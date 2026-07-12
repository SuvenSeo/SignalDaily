# SignalDaily

SignalDaily is a daily intelligence archive for AI, technology, coding tools, Sri Lankan markets, CSE-related developments, global markets, and future opportunities.

The repo is optimized for a **ChatGPT Agent-first workflow**. The agent researches and writes the daily intelligence brief. GitHub stores the permanent archive, templates, operating rules, source map, quality checks, and automation scaffolding.

## Current operating model

```text
ChatGPT Agent
  -> researches current sources
  -> writes a GitHub-ready Markdown brief
  -> commits daily/YYYY-MM-DD.md when GitHub writing is available
  -> prepares a Telegram-ready alert
  -> updates the long-term intelligence archive
```

This setup does **not** require OpenAI API credits.

## What makes a good SignalDaily brief

A strong brief answers:

- What changed?
- Why does it matter?
- Who is affected?
- What should Seo watch next?
- What can Seo build, learn, or research from this?

Every brief should separate facts from interpretation, use source links, avoid hype, and avoid direct financial advice.

## Repository structure

```text
SignalDaily/
├── AGENT.md
├── DISCLAIMER.md
├── OPERATIONS.md
├── PROMPTS.md
├── README.md
├── SECURITY.md
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   └── pull_request_template.md
├── daily/
├── docs/
│   ├── product-roadmap.md
│   ├── quality-standard.md
│   └── telegram-integration.md
├── ideas/
├── monthly/
├── scripts/
│   └── validate_repo.py
├── templates/
├── topics/
├── updates/
└── weekly/
```

## Daily report location

Daily reports should be saved as:

```text
daily/YYYY-MM-DD.md
```

Example:

```text
daily/2026-07-12.md
```

## Daily report sections

Each brief should include:

1. Executive Summary
2. AI & Models
3. Coding & Developer Tools
4. Sri Lanka / CSE / Economy
5. Global Markets
6. Opportunity Radar
7. Deep Dive of the Day
8. Watchlist for Tomorrow
9. GitHub-Ready Output
10. Sources

## Quality gate

Run the validator locally or through GitHub Actions:

```bash
python scripts/validate_repo.py
```

The validator checks required files, Markdown hygiene, daily filename format, required daily sections, source count warnings, and unsafe financial-advice wording.

## Automation

The repo includes two GitHub Actions workflows:

| Workflow | Purpose |
|---|---|
| `Repo Quality` | Runs the repository validator on pushes, pull requests, and manual dispatch. |
| `Daily SignalDaily Reminder` | Creates a daily GitHub issue at 06:00 Asia/Colombo and optionally sends a Telegram reminder if secrets are configured. |

## Telegram

See `docs/telegram-integration.md`.

Optional repository secrets:

| Secret | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Target chat, group, or channel ID. |

## Non-negotiable rules

- Use current web research.
- Cite sources for factual claims.
- Prefer official sources for CSE, CBSL, SEC Sri Lanka, listed-company announcements, OpenAI, Anthropic, Google, Meta, Microsoft, and GitHub.
- Separate facts from interpretation.
- Mark uncertainty clearly.
- Do not give direct buy/sell financial advice.
- Avoid hype.
- Keep output concise, useful, and GitHub-ready.

## Upgrade path

Later, this repo can be upgraded to a full API-powered pipeline:

```text
GitHub Actions -> Python collector -> OpenAI API -> Markdown report -> commit -> Telegram alert
```

Until API credits are available, the stable path is:

```text
GitHub Actions reminder -> ChatGPT Agent run -> GitHub archive -> Telegram alert
```
