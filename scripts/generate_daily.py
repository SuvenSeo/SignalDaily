#!/usr/bin/env python3
"""Generate SignalDaily daily Markdown from free public APIs.

No paid LLM API is required. The script is intentionally standard-library only
so GitHub Actions can run it without dependency installation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
UA = "SignalDaily/1.0 (+https://github.com/SuvenSeo/SignalDaily)"
TITLE_DASH = "\u2014"
MAX_PER_SECTION = 6
SECTIONS = [
    "AI & Models",
    "Coding & Developer Tools",
    "Sri Lanka / CSE / Economy",
    "Global Markets",
]


def today_colombo() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Colombo")).strftime("%Y-%m-%d")


def clean(value: Any, limit: int = 320) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    out = {"User-Agent": UA, "Accept": "application/json,application/xml,text/xml,text/plain,*/*"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        out["Authorization"] = f"Bearer {token}"
    if extra:
        out.update(extra)
    return out


def url(base: str, params: dict[str, Any]) -> str:
    return base + "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})


def fetch_bytes(address: str, timeout: int = 20) -> bytes:
    if os.getenv("SIGNALDAILY_DISABLE_NETWORK") == "1":
        raise RuntimeError("network disabled")
    req = urllib.request.Request(address, headers=headers())
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310 - fixed public API URLs
        return response.read()


def fetch_json(address: str) -> Any:
    return json.loads(fetch_bytes(address).decode("utf-8", errors="replace"))


def fetch_text(address: str) -> str:
    return fetch_bytes(address).decode("utf-8", errors="replace")


def parse_date(value: str | None) -> float:
    if not value:
        return 0.0
    for parser in (
        lambda v: dt.datetime.fromisoformat(v.replace("Z", "+00:00")),
        email.utils.parsedate_to_datetime,
    ):
        try:
            parsed = parser(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc).timestamp()
        except Exception:
            pass
    return 0.0


def item(section: str, title: str, link: str, source: str, **kw: Any) -> dict[str, Any]:
    return {
        "section": section,
        "title": clean(title, 180),
        "url": str(link or "").strip(),
        "source": source,
        "published": kw.get("published"),
        "summary": clean(kw.get("summary"), 320),
        "metric": clean(kw.get("metric"), 160),
        "score": float(kw.get("score") or 0),
        "tags": kw.get("tags") or [],
    }


def safe(name: str, fn) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    started = time.time()
    try:
        values = fn()
        return values, [], {name: {"status": "ok", "seconds": round(time.time() - started, 2), "items": len(values)}}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError, ET.ParseError) as exc:
        return [], [f"{name}: {type(exc).__name__}: {exc}"], {name: {"status": "failed"}}
    except Exception as exc:
        return [], [f"{name}: unexpected {type(exc).__name__}: {exc}"], {name: {"status": "failed"}}


def collect_hn(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in source.get("queries", []):
        data = fetch_json(url("https://hn.algolia.com/api/v1/search_by_date", {
            "query": q.get("query"), "tags": "story", "hitsPerPage": q.get("limit", 8)
        }))
        for hit in data.get("hits", []):
            title = hit.get("title") or hit.get("story_title")
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            if title and link:
                points = int(hit.get("points") or 0)
                comments = int(hit.get("num_comments") or 0)
                out.append(item(
                    q.get("section", "Coding & Developer Tools"), title, link, "Hacker News / Algolia",
                    published=hit.get("created_at"), metric=f"{points} points, {comments} comments",
                    summary=hit.get("story_text") or hit.get("comment_text"), score=points + comments * 1.5,
                    tags=["community-signal"]
                ))
    return out


def collect_arxiv(source: dict[str, Any]) -> list[dict[str, Any]]:
    data = fetch_text(url("https://export.arxiv.org/api/query", {
        "search_query": source.get("query"),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": source.get("limit", 8),
    }))
    root = ET.fromstring(data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    out: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        link = ""
        for node in entry.findall("atom:link", ns):
            if node.attrib.get("rel") in ("alternate", None):
                link = node.attrib.get("href", "")
                break
        authors = [clean(a.findtext("atom:name", default="", namespaces=ns), 80) for a in entry.findall("atom:author", ns)]
        title = entry.findtext("atom:title", default="", namespaces=ns)
        if title and link:
            out.append(item(
                "AI & Models", title, link, "arXiv",
                published=entry.findtext("atom:published", default="", namespaces=ns),
                summary=entry.findtext("atom:summary", default="", namespaces=ns),
                metric=", ".join([a for a in authors[:3] if a]), score=50, tags=["research"]
            ))
    return out


def collect_github(source: dict[str, Any]) -> list[dict[str, Any]]:
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(source.get("created_within_days", 21)))).date().isoformat()
    query = f"{source.get('query', 'topic:ai stars:>25')} created:>={since}"
    data = fetch_json(url("https://api.github.com/search/repositories", {
        "q": query, "sort": "stars", "order": "desc", "per_page": source.get("limit", 8)
    }))
    out: list[dict[str, Any]] = []
    for repo in data.get("items", []):
        stars = int(repo.get("stargazers_count") or 0)
        forks = int(repo.get("forks_count") or 0)
        out.append(item(
            "Coding & Developer Tools", repo.get("full_name"), repo.get("html_url"), "GitHub Search API",
            published=repo.get("created_at") or repo.get("updated_at"), summary=repo.get("description"),
            metric=f"{stars} stars, {forks} forks", score=stars + forks * 2, tags=["open-source"]
        ))
    return [x for x in out if x["title"] and x["url"]]


def collect_gdelt(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in source.get("queries", []):
        data = fetch_json(url("https://api.gdeltproject.org/api/v2/doc/doc", {
            "query": q.get("query"), "mode": "ArtList", "format": "json",
            "maxrecords": q.get("limit", 6), "sort": "HybridRel", "timespan": q.get("timespan", source.get("timespan", "2d"))
        }))
        for article in data.get("articles", []):
            title, link = article.get("title"), article.get("url")
            domain = clean(article.get("domain"), 80) or "GDELT"
            if title and link:
                out.append(item(
                    q.get("section", "Global Markets"), title, link, f"GDELT / {domain}",
                    published=article.get("seendate") or article.get("date"), summary=article.get("sourcecountry"),
                    metric=domain, score=40, tags=["news"]
                ))
    return out


def collect_fx(source: dict[str, Any]) -> list[dict[str, Any]]:
    base = source.get("base", "USD")
    data = fetch_json(f"https://open.er-api.com/v6/latest/{urllib.parse.quote(base)}")
    rates = data.get("rates", {})
    parts = []
    for target in source.get("targets", ["LKR", "EUR", "GBP", "JPY", "INR"]):
        if target in rates:
            parts.append(f"{base}/{target}: {rates[target]}")
    return [item(
        "Sri Lanka / CSE / Economy", f"FX snapshot from open exchange-rate API ({base})",
        "https://open.er-api.com/v6/latest/USD", "ExchangeRate-API open endpoint",
        published=data.get("time_last_update_utc"), summary="; ".join(parts), metric=data.get("result"),
        score=45, tags=["fx", "market-data"]
    )]


def collect_coingecko(source: dict[str, Any]) -> list[dict[str, Any]]:
    data = fetch_json(url("https://api.coingecko.com/api/v3/simple/price", {
        "ids": ",".join(source.get("ids", ["bitcoin", "ethereum", "solana"])),
        "vs_currencies": ",".join(source.get("vs_currencies", ["usd", "lkr"])),
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }))
    lines, latest = [], None
    for coin, values in data.items():
        latest = values.get("last_updated_at") or latest
        bits = [coin]
        if values.get("usd") is not None:
            bits.append(f"USD {values.get('usd')}")
        if values.get("lkr") is not None:
            bits.append(f"LKR {values.get('lkr')}")
        if values.get("usd_24h_change") is not None:
            bits.append(f"24h {values.get('usd_24h_change'):.2f}%")
        lines.append(" - ".join(bits))
    published = dt.datetime.fromtimestamp(latest, tz=dt.timezone.utc).isoformat() if latest else None
    return [item(
        "Global Markets", "Crypto price snapshot from CoinGecko", "https://www.coingecko.com/",
        "CoinGecko API", published=published, summary="; ".join(lines), metric="simple price endpoint",
        score=42, tags=["crypto", "market-data"]
    )]


def collect(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    collectors = {"hn": collect_hn, "arxiv": collect_arxiv, "github": collect_github, "gdelt": collect_gdelt, "fx": collect_fx, "coingecko": collect_coingecko}
    items: list[dict[str, Any]] = []
    failures: list[str] = []
    diagnostics: dict[str, Any] = {}
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        fn = collectors.get(source.get("type"))
        if not fn:
            failures.append(f"{source.get('name')}: unsupported source type {source.get('type')}")
            continue
        got, failed, diag = safe(source.get("name", source.get("type")), lambda s=source, f=fn: f(s))
        items.extend(got)
        failures.extend(failed)
        diagnostics.update(diag)
        time.sleep(float(source.get("pause_seconds", 0.2)))
    return dedupe(items), failures, diagnostics


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in sorted(items, key=lambda x: (float(x.get("score") or 0), parse_date(x.get("published"))), reverse=True):
        key = (it.get("url") or it.get("title") or "").split("?", 1)[0].lower()
        if key and key not in seen and it.get("title") and it.get("url"):
            seen.add(key)
            out.append(it)
    return out


def by_section(items: list[dict[str, Any]], section: str) -> list[dict[str, Any]]:
    selected = [x for x in items if x.get("section") == section]
    return sorted(selected, key=lambda x: (float(x.get("score") or 0), parse_date(x.get("published"))), reverse=True)[:MAX_PER_SECTION]


def bullet(it: dict[str, Any]) -> str:
    parts = [f"**[{it['title']}]({it['url']})**"]
    if it.get("metric"):
        parts.append(f"Signal: {it['metric']}.")
    if it.get("summary"):
        parts.append(clean(it["summary"], 260).rstrip(".") + ".")
    if it.get("published"):
        parts.append(f"Seen/published: {it['published']}.")
    parts.append(f"Source: {it['source']}.")
    return "- " + " ".join(parts)


def fallback(section: str) -> str:
    fallbacks = {
        "AI & Models": "- No strong API item was collected for AI today. Review official lab blogs and arXiv manually before making high-impact claims.",
        "Coding & Developer Tools": "- No strong developer-tool item was collected. Check GitHub Trending, major framework release feeds, and HN manually.",
        "Sri Lanka / CSE / Economy": "- No strong local-market item was collected. Verify CSE/CBSL/SEC Sri Lanka primary sources manually; this is educational only, not financial advice.",
        "Global Markets": "- No strong global-market item was collected. Treat market data as delayed and verify prices against primary market-data sources.",
    }
    return fallbacks[section]


def exec_summary(items: list[dict[str, Any]], failures: list[str]) -> list[str]:
    top = sorted(items, key=lambda x: (float(x.get("score") or 0), parse_date(x.get("published"))), reverse=True)[:5]
    lines = []
    for i, it in enumerate(top, 1):
        why = it.get("summary") or it.get("metric") or "Collected as a high-signal item from configured API sources."
        lines.append(f"{i}. **{it['title']}** - {clean(why, 220)}")
    while len(lines) < 5:
        lines.append(f"{len(lines) + 1}. **Manual verification needed** - APIs returned limited data for this slot; check primary sources before treating the day as complete.")
    if failures:
        lines.append(f"- Collection warning: {len(failures)} source(s) failed or returned invalid data; see Automation Notes.")
    return lines


def opportunities(items: list[dict[str, Any]]) -> list[str]:
    ai = by_section(items, "AI & Models")
    dev = by_section(items, "Coding & Developer Tools")
    local = by_section(items, "Sri Lanka / CSE / Economy")
    lead = (ai or dev or local or [{}])[0]
    return [
        "- **Project idea 1:** Build a source reliability dashboard that scores every SignalDaily item by freshness, source type, and duplicate confirmation.",
        "- **Project idea 2:** Turn high-signal GitHub repos into weekly learning cards: what it does, stack used, why it is trending, and clone-worthy ideas.",
        "- **Project idea 3:** Add an archive search script that indexes every `daily/*.md` report and surfaces recurring themes.",
        "- **SaaS idea 1:** Sri Lanka-focused SME intelligence digest that monitors official notices, FX movement, tax/regulatory changes, and sector opportunities.",
        "- **SaaS idea 2:** Developer trend radar for teams: HN + GitHub + arXiv + release feeds converted into concise engineering briefs.",
        f"- **Sri Lanka-specific opportunity:** Track '{(local[0]['title'] if local else 'official CBSL/CSE updates')}' and convert verified changes into educational explainers, not financial recommendations.",
        f"- **Market-research idea, educational only:** Watch whether '{lead.get('title', 'today\'s leading signal')}' develops into measurable adoption, spending, or risk impact.",
    ]


def deep_dive(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return [
            "**Topic:** Automation resilience.",
            "- **What happened:** The pipeline generated a report even with limited source data.",
            "- **Why it matters:** A stable archive is more useful than a fragile perfect system.",
            "- **Who is affected:** Seo and future readers relying on daily continuity.",
            "- **What to watch next:** Source failures, missing categories, and duplicate URLs.",
            "- **How Seo can use it:** Improve collectors one source at a time instead of waiting for a paid LLM stack.",
        ]
    it = sorted(items, key=lambda x: float(x.get("score") or 0), reverse=True)[0]
    return [
        f"**Topic:** [{it['title']}]({it['url']})",
        f"- **What happened:** {it.get('summary') or 'A configured source returned this as one of the highest-ranked items today.'}",
        "- **Why it matters:** It may indicate a practical shift in AI, developer tools, local markets, or global risk depending on follow-up verification.",
        "- **Who is affected:** Builders, learners, analysts, and anyone tracking the relevant technology or market segment.",
        "- **What to watch next:** Look for primary-source confirmation, follow-up announcements, adoption metrics, and contradictory reporting.",
        "- **How Seo can use it:** Convert the signal into a small research note, coding experiment, or source-tracking improvement.",
    ]


def sources(items: list[dict[str, Any]], config: dict[str, Any]) -> list[str]:
    out, seen = [], set()
    for it in items:
        link = it.get("url")
        if link and link not in seen:
            seen.add(link)
            out.append(f"- {it.get('source')}: {link}")
    for ref in config.get("reference_sources", []):
        link = ref.get("url")
        if link and link not in seen:
            seen.add(link)
            out.append(f"- {ref.get('name', 'Reference')}: {link}")
    return out[:40]


def render(date: str, items: list[dict[str, Any]], failures: list[str], diagnostics: dict[str, Any], config: dict[str, Any]) -> str:
    lines = [f"# SignalDaily Intelligence Brief {TITLE_DASH} {date}", "", "Generated by the API-powered SignalDaily pipeline. Educational only; not financial advice.", ""]
    lines += ["## Executive Summary", *exec_summary(items, failures), ""]
    for section in SECTIONS:
        lines.append(f"## {section}")
        rows = by_section(items, section)
        lines.extend([bullet(x) for x in rows] if rows else [fallback(section)])
        if section == "Sri Lanka / CSE / Economy":
            lines += ["", "Educational boundary: this section may discuss market context, but it does not recommend buying, selling, holding, or trading any security or asset."]
        lines.append("")
    lines += ["## Opportunity Radar", *opportunities(items), ""]
    lines += ["## Deep Dive of the Day", *deep_dive(items), ""]
    lines += ["## Watchlist for Tomorrow",
              "- Check official AI lab blogs and GitHub releases for primary confirmation.",
              "- Review CBSL, CSE, SEC Sri Lanka, and listed-company announcements before treating local-market items as complete.",
              "- Verify market data after the next market close; weekend or holiday data may be stale.",
              "- Scan whether collected GitHub repositories keep gaining stars or ship new releases."]
    if failures:
        lines.append("- Fix or replace failed API sources listed in Automation Notes.")
    lines += ["", "## GitHub-Ready Output",
              f"1. Suggested file path: `daily/{date}.md`",
              f"2. Suggested commit message: `daily: add SignalDaily brief for {date}`",
              "3. Telegram-ready alert message:", "", "```text",
              f"SignalDaily - {date}",
              f"Generated {len(items)} API-backed signals across AI, dev tools, Sri Lanka/CSE/economy, and global markets.",
              f"Full report: daily/{date}.md", "Educational only; not financial advice.", "```", ""]
    lines += ["## Automation Notes", f"- Items collected: {len(items)}", f"- Source failures: {len(failures)}"]
    lines.extend([f"- Failure: {x}" for x in failures[:10]])
    lines.extend([f"- {name}: {data}" for name, data in sorted(diagnostics.items())])
    lines += ["", "## Sources", *(sources(items, config) or ["- SignalDaily source registry: config/sources.json"]), ""]
    return "\n".join(lines)


def write_pack(path: Path, date: str, items: list[dict[str, Any]], failures: list[str], diagnostics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "date": date,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "item_count": len(items),
        "failures": failures,
        "diagnostics": diagnostics,
        "items": items,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the daily SignalDaily API-backed brief.")
    parser.add_argument("--date", default=today_colombo())
    parser.add_argument("--config", default=str(ROOT / "config" / "sources.json"))
    parser.add_argument("--output")
    parser.add_argument("--source-pack")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{2}-[01]\d-[0-3]\d", args.date):
        raise SystemExit("--date must use YYYY-MM-DD format")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    items, failures, diagnostics = collect(config)
    report = render(args.date, items, failures, diagnostics, config)
    output = Path(args.output) if args.output else ROOT / "daily" / f"{args.date}.md"
    pack = Path(args.source_pack) if args.source_pack else ROOT / "source-packs" / f"{args.date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    write_pack(pack, args.date, items, failures, diagnostics)
    if args.print:
        print(report)
    print(f"Wrote {output}")
    print(f"Wrote {pack}")
    print(f"Collected {len(items)} item(s), {len(failures)} failure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
