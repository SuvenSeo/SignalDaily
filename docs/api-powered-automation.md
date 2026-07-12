# API-Powered SignalDaily Automation

SignalDaily now has a no-paid-LLM automation path. GitHub Actions can fetch free/no-key or built-in-token public APIs, generate Markdown hourly updates, validate the repo, commit the files, and optionally send a Telegram alert.

## What this does

```text
GitHub Actions hourly schedule
  -> scripts/generate_hourly.py
  -> free public APIs from config/hourly-sources.json
  -> updates/YYYY-MM-DD-HHMM.md
  -> source-packs/YYYY-MM-DD-HHMM.json
  -> scripts/validate_repo.py
  -> git commit + push
  -> optional Telegram alert
```

The generated update is deterministic and extractive. It does not use the OpenAI API, so it avoids API-credit cost. It is not as smart as a full ChatGPT Agent brief, but it gives a stable source-backed base layer that can run 24 times per day.

## Workflow

The workflow file is:

```text
.github/workflows/daily-api-brief.yml
```

Default schedule:

```text
Every hour at minute 17 UTC
```

Because Sri Lanka is UTC+05:30, this still equals one run every hour in Asia/Colombo time. The minute is offset from the top of the hour to reduce API congestion.

Manual run:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Hourly API SignalDaily Brief**.
4. Click **Run workflow**.
5. Optionally enter:
   - `report_date` in `YYYY-MM-DD` format
   - `report_slot` in `YYYY-MM-DD-HHMM` format
   - `report_kind` as `hourly` or `daily`

## Why hourly output goes to `updates/`

A 24-times-per-day workflow should not overwrite the same `daily/YYYY-MM-DD.md` file every hour. The hourly mode writes immutable files instead:

```text
updates/YYYY-MM-DD-HHMM.md
source-packs/YYYY-MM-DD-HHMM.json
```

If you manually choose `report_kind=daily`, the workflow writes:

```text
daily/YYYY-MM-DD.md
source-packs/YYYY-MM-DD.json
```

## Source registry

The source registry is:

```text
config/hourly-sources.json
```

Configured source types:

| Source type | Purpose | Key required |
|---|---|---|
| `hn` | AI/dev community signals from Hacker News Algolia | No |
| `arxiv` | Recent AI, ML, NLP, CV, and software-engineering papers | No |
| `github` | Newly created AI/agent/dev-tool repositories | No, but `GITHUB_TOKEN` improves rate limits |
| `github_releases` | Releases from major developer and AI repositories | No, uses built-in `GITHUB_TOKEN` when available |
| `github_advisories` | Security advisories affecting developer dependencies | No, uses built-in `GITHUB_TOKEN` when available |
| `gdelt` | Global news discovery for AI, Sri Lanka, and markets | No |
| `devto` | Developer articles from DEV/Forem | No |
| `stackexchange` | Hot developer questions from Stack Overflow | No |
| `rss` | Official/engineering feeds where stable RSS/Atom exists | No |
| `pypi` | Python package release context | No |
| `npm` | JavaScript/TypeScript package release context | No |
| `cisa_kev` | Known exploited vulnerability feed | No |
| `worldbank` | Sri Lanka macro indicators | No; daily profile only |
| `fx` | USD/LKR and other FX snapshots | No |
| `coingecko` | Crypto price context | No, but can be rate-limited |
| `stooq` | Global index, stock, commodity, and FX-like quote snapshots | No |
| `open_meteo` | Colombo operating-context weather | No |

## Profiles

Each source can declare profiles:

```json
"profiles": ["hourly", "daily"]
```

Hourly runs use `profile=hourly`. Manual daily runs use `profile=daily`. Slow-moving sources, such as World Bank macro indicators, can be set to daily only to avoid noise.

## Telegram

Telegram is optional. Add these repository secrets only if you want alerts:

| Secret | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Chat, group, or channel ID |

If the secrets are missing, the workflow still generates and commits the report.

## Failure behavior

The generator uses fail-soft behavior. If one API fails, the update still gets created with an **Automation Notes** section listing failures. The workflow creates a GitHub issue only when the whole job fails, for example because validation fails or GitHub cannot push.

## Rate-limit discipline

Hourly automation is useful, but more APIs does not automatically mean better intelligence. The source registry keeps per-source limits small and deduplicates by URL. If a source starts failing repeatedly, reduce its limits, move it to daily-only, or disable it until the schema/rate-limit issue is fixed.

## Market-content boundary

The report can include FX, crypto, CSE, macro, and market context, but it must remain educational. It must not recommend buying, selling, holding, shorting, or trading any security or asset.

## How to improve later

High-value next upgrades:

1. Add official CBSL and CSE collectors if stable machine-readable endpoints are identified.
2. Add a weekly rollup generator using the committed `source-packs/*.json` files.
3. Add a topic index builder that tracks recurring companies, models, repositories, vulnerabilities, packages, and macro themes.
4. Add duplicate clustering across hourly updates so repeated stories do not dominate the archive.
5. Add an LLM summarizer only after API credits are available, using the source pack as grounded input.
