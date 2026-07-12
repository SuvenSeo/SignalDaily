# API-Powered SignalDaily Automation

SignalDaily now has a no-paid-LLM automation path. GitHub Actions can fetch free/no-key public APIs, generate a Markdown daily brief, validate it, commit it to `daily/YYYY-MM-DD.md`, and optionally send a Telegram alert.

## What this does

```text
GitHub Actions schedule
  -> scripts/generate_daily.py
  -> free public APIs from config/sources.json
  -> daily/YYYY-MM-DD.md
  -> source-packs/YYYY-MM-DD.json
  -> scripts/validate_repo.py
  -> git commit + push
  -> optional Telegram alert
```

The generated brief is deterministic and extractive. It does not use the OpenAI API, so it avoids API-credit cost. It is not as smart as a full ChatGPT Agent brief, but it gives a stable daily base report and source pack.

## Workflow

The workflow file is:

```text
.github/workflows/daily-api-brief.yml
```

Default schedule:

```text
06:15 Asia/Colombo every day
```

Manual run:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Daily API SignalDaily Brief**.
4. Click **Run workflow**.
5. Optionally enter a `report_date` in `YYYY-MM-DD` format.

## Source registry

The source registry is:

```text
config/sources.json
```

Currently configured source types:

| Source type | Purpose | Key required |
|---|---:|---:|
| `hn` | AI/dev community signals from Hacker News Algolia | No |
| `arxiv` | Recent AI, ML, NLP, and software engineering papers | No |
| `github` | Recently created AI/dev-tool repositories | No, but `GITHUB_TOKEN` improves rate limits |
| `gdelt` | Global news discovery for AI, Sri Lanka, and markets | No |
| `fx` | USD/LKR and other FX snapshots | No |
| `coingecko` | Crypto price context | No |

## Output files

Every successful run writes:

```text
daily/YYYY-MM-DD.md
source-packs/YYYY-MM-DD.json
```

The Markdown file is the human-readable daily brief. The JSON source pack preserves structured raw signal data, source failures, and diagnostics so the system can be improved later.

## Telegram

Telegram is optional. Add these repository secrets only if you want alerts:

| Secret | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Chat, group, or channel ID |

If the secrets are missing, the workflow still generates and commits the report.

## Failure behavior

The generator uses fail-soft behavior. If one API fails, the report still gets created with an **Automation Notes** section listing failures. The workflow creates a GitHub issue only when the whole job fails, for example because validation fails or GitHub cannot push.

## Market-content boundary

The daily report can include FX, crypto, CSE, macro, and market context, but it must remain educational. It must not recommend buying, selling, holding, shorting, or trading any security or asset.

## How to improve later

High-value next upgrades:

1. Add official CBSL and CSE collectors if stable machine-readable endpoints are identified.
2. Add RSS collectors for official AI lab blogs and developer changelogs.
3. Add a weekly rollup generator using the committed `source-packs/*.json` files.
4. Add a topic index builder that tracks recurring companies, models, repositories, and macro themes.
5. Add an LLM summarizer only after API credits are available, using the source pack as grounded input.
