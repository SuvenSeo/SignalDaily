# SignalDaily

SignalDaily is a daily intelligence archive for AI, technology, coding tools, Sri Lankan markets, CSE-related developments, global markets, and future opportunities.

This repository is designed to work with a ChatGPT Agent rather than the OpenAI API. The agent researches and writes daily briefs. This repo stores the final reports, templates, topic indexes, and operating rules.

## Core workflow

```text
ChatGPT Agent
  -> researches current sources
  -> writes a GitHub-ready Markdown brief
  -> provides file path, commit message, and Telegram-ready alert
  -> report is committed to this repo
```

## Repository structure

```text
SignalDaily/
├── AGENT.md
├── PROMPTS.md
├── README.md
├── daily/
├── weekly/
├── monthly/
├── topics/
├── ideas/
└── templates/
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

## Non-negotiable rules

- Use current web research.
- Cite sources for factual claims.
- Prefer official sources for CSE, CBSL, SEC Sri Lanka, listed-company announcements, OpenAI, Anthropic, Google, Meta, Microsoft, and GitHub.
- Separate facts from interpretation.
- Mark uncertainty clearly.
- Do not give direct buy/sell financial advice.
- Avoid hype.
- Keep output concise, useful, and GitHub-ready.

## Current operating model

This repo is currently optimized for the no-API setup:

```text
ChatGPT Agent = research and write
GitHub repo = permanent archive
Telegram = short alert message prepared by the agent
```

Later, this repo can be upgraded to a full GitHub Actions + OpenAI API automation if API credits become available.
