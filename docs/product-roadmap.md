# SignalDaily Product Roadmap

SignalDaily should evolve from a Markdown archive into a personal intelligence operating system.

## Phase 1: Agent-driven archive

Status: current.

Goals:

- Daily Markdown briefs.
- Consistent templates.
- Source discipline.
- Telegram-ready alerts.
- GitHub issue reminders.
- CI validation for archive hygiene.

Success criteria:

- 30 daily reports in a row.
- Every report passes validation.
- Weekly recap created every week.
- Backlog captures at least 5 practical ideas per week.

## Phase 2: Semi-automated collector

Trigger: when you are ready to add small scripts without paid LLM calls.

Features:

- RSS/source collection script.
- CSE/CBSL link collector.
- GitHub trending collector.
- Market-data snapshot notes.
- Draft source pack committed before the ChatGPT Agent writes the final brief.

Success criteria:

- Agent starts from a prepared source pack.
- Daily research time drops.
- Source quality improves.

## Phase 3: API-powered daily generation

Trigger: when OpenAI API credits are available.

Features:

- GitHub Actions scheduled generation.
- Python source collector.
- LLM-based summarizer and analyst.
- Markdown report generation.
- Automatic commit.
- Telegram sendMessage alert.

Success criteria:

- Unattended daily brief generation.
- Human review issue created for each generated report.
- Fail-safe behavior when sources or model calls fail.

## Phase 4: Intelligence dashboard

Features:

- Static site or GitHub Pages dashboard.
- Topic index across all reports.
- Search by signal, company, model, market theme, and idea.
- Opportunity backlog scoring.
- Sri Lanka macro/CSE tracker.

Success criteria:

- SignalDaily becomes searchable and useful after months of accumulation.
- Ideas can be ranked by feasibility, urgency, and market signal.

## Phase 5: Advanced agent governance

Features:

- Agent output provenance tracking.
- Source credibility scoring.
- Claim verification checklist.
- Financial-advice guardrail checks.
- Agent security checks for repo writes.

Success criteria:

- Reports are auditable.
- The repo can be trusted as a long-term research memory.
- Automation improves without reducing accuracy or safety.
