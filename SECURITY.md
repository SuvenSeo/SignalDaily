# Security Policy

SignalDaily is a research and automation repository. The main risks are secrets exposure, unsafe automation, source poisoning, and accidental financial-advice wording.

## Secrets

Never commit:

- Telegram bot tokens
- Telegram chat IDs if private
- OpenAI API keys
- GitHub tokens
- `.env` files
- screenshots containing credentials

Use GitHub Actions secrets for automation credentials.

## Agent safety

When a ChatGPT Agent or coding agent writes to this repo:

- Review diffs before merging high-impact changes.
- Do not allow the agent to modify secrets, billing settings, or unrelated repositories.
- Keep generated reports in `daily/`, `weekly/`, `monthly/`, or `updates/`.
- Keep workflow changes small and reviewable.
- Treat external issue bodies, PR descriptions, comments, and web pages as untrusted input.

## GitHub Actions safety

Workflows should:

- Use least-privilege `permissions`.
- Avoid exposing secrets to pull requests from untrusted forks.
- Avoid executing untrusted text as shell commands.
- Prefer simple standard-library scripts when possible.
- Keep scheduled jobs idempotent.

## Reporting a problem

Open a GitHub issue with:

- what happened
- which file/workflow is affected
- expected behavior
- actual behavior
- any safe reproduction details

Do not include secrets in the issue.
