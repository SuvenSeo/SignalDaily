#!/usr/bin/env python3
"""High-volume hourly SignalDaily generator.

This extends generate_daily.py with more public/free collectors while keeping the
main daily generator simple. It uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import generate_daily as base

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ["AI & Models", "Coding & Developer Tools", "Sri Lanka / CSE / Economy", "Global Markets"]


def now_colombo() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("Asia/Colombo"))


def slot_colombo() -> str:
    return now_colombo().strftime("%Y-%m-%d-%H00")


def date_colombo() -> str:
    return now_colombo().strftime("%Y-%m-%d")


def iso_epoch(value: int | float | None) -> str | None:
    if value is None:
        return None
    if value > 1_000_000_000_000:
        value = value / 1000
    return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).isoformat()


def collect_github_releases(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for repo in source.get("repos", []):
        data = base.fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page={int(source.get('limit_per_repo', 1))}")
        for release in data[: int(source.get("limit_per_repo", 1))]:
            out.append(base.item(
                source.get("section", "Coding & Developer Tools"),
                f"{repo} release: {release.get('name') or release.get('tag_name')}",
                release.get("html_url"),
                "GitHub Releases API",
                published=release.get("published_at"),
                summary=release.get("body"),
                metric=release.get("tag_name"),
                score=60,
                tags=["release", "open-source"],
            ))
    return out


def collect_github_advisories(source: dict[str, Any]) -> list[dict[str, Any]]:
    data = base.fetch_json(base.url("https://api.github.com/advisories", {
        "per_page": source.get("limit", 8), "sort": "published", "direction": "desc"
    }))
    scores = {"critical": 90, "high": 75, "medium": 55, "low": 35}
    out: list[dict[str, Any]] = []
    for adv in data[: int(source.get("limit", 8))]:
        severity = adv.get("severity") or "unknown"
        out.append(base.item(
            "Coding & Developer Tools",
            f"{adv.get('ghsa_id', 'GHSA')}: {adv.get('summary')}",
            adv.get("html_url"),
            "GitHub Security Advisories API",
            published=adv.get("published_at"),
            summary=adv.get("description"),
            metric=f"Severity: {severity}",
            score=scores.get(severity, 40),
            tags=["security", "dependency-risk"],
        ))
    return out


def collect_devto(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tag in source.get("tags", ["ai", "programming"]):
        data = base.fetch_json(base.url("https://dev.to/api/articles", {
            "tag": tag, "top": source.get("top_days", 1), "per_page": source.get("limit_per_tag", 4)
        }))
        for article in data:
            reactions = int(article.get("public_reactions_count") or article.get("positive_reactions_count") or 0)
            comments = int(article.get("comments_count") or 0)
            out.append(base.item(
                "Coding & Developer Tools",
                article.get("title"),
                article.get("url"),
                "DEV/Forem Articles API",
                published=article.get("published_at") or article.get("published_timestamp"),
                summary=article.get("description"),
                metric=f"tag {tag}, {reactions} reactions, {comments} comments",
                score=reactions + comments * 2,
                tags=["developer-writing", tag],
            ))
    return out


def collect_stackexchange(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    site = source.get("site", "stackoverflow")
    for spec in source.get("tag_sets", []):
        tagged = ";".join(spec.get("tags", []))
        data = base.fetch_json(base.url("https://api.stackexchange.com/2.3/questions", {
            "site": site, "tagged": tagged, "sort": spec.get("sort", "hot"), "order": "desc",
            "pagesize": spec.get("limit", 5), "filter": "default",
        }))
        for q in data.get("items", []):
            score = int(q.get("score") or 0)
            answers = int(q.get("answer_count") or 0)
            out.append(base.item(
                "Coding & Developer Tools",
                q.get("title"),
                q.get("link"),
                "Stack Exchange API",
                published=iso_epoch(q.get("creation_date")),
                summary="Stack Overflow question trend/discussion signal.",
                metric=f"tags {tagged}, score {score}, answers {answers}",
                score=score + answers * 2,
                tags=["q-and-a", "developer-signal"],
            ))
    return out


def collect_rss(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for feed in source.get("feeds", []):
        root = ET.fromstring(base.fetch_text(feed.get("url")))
        if root.find("channel") is not None:
            entries = root.findall("./channel/item")
            for entry in entries[: int(feed.get("limit", source.get("limit_per_feed", 3)))]:
                title = entry.findtext("title", default="")
                link = entry.findtext("link", default="")
                if title and link:
                    out.append(base.item(
                        feed.get("section", source.get("section", "AI & Models")),
                        title,
                        link,
                        feed.get("name", "RSS feed"),
                        published=entry.findtext("pubDate", default=""),
                        summary=entry.findtext("description", default=""),
                        metric="RSS",
                        score=55,
                        tags=["rss", "primary-or-official"],
                    ))
        else:
            entries = root.findall("atom:entry", ns)
            for entry in entries[: int(feed.get("limit", source.get("limit_per_feed", 3)))]:
                title = entry.findtext("atom:title", default="", namespaces=ns)
                link = ""
                for link_node in entry.findall("atom:link", ns):
                    if link_node.attrib.get("rel") in ("alternate", None):
                        link = link_node.attrib.get("href", "")
                        break
                if title and link:
                    out.append(base.item(
                        feed.get("section", source.get("section", "AI & Models")),
                        title,
                        link,
                        feed.get("name", "Atom feed"),
                        published=entry.findtext("atom:updated", default="", namespaces=ns) or entry.findtext("atom:published", default="", namespaces=ns),
                        summary=entry.findtext("atom:summary", default="", namespaces=ns) or entry.findtext("atom:content", default="", namespaces=ns),
                        metric="Atom/RSS",
                        score=55,
                        tags=["rss", "primary-or-official"],
                    ))
    return out


def collect_pypi(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for package in source.get("packages", []):
        data = base.fetch_json(f"https://pypi.org/pypi/{urllib.parse.quote(package)}/json")
        info = data.get("info", {})
        version = info.get("version")
        releases = data.get("releases", {}).get(version, []) if version else []
        dates = [base.parse_date(x.get("upload_time_iso_8601")) for x in releases if x.get("upload_time_iso_8601")]
        published = iso_epoch(max(dates)) if dates else None
        out.append(base.item(
            "Coding & Developer Tools",
            f"PyPI package update: {package} {version}",
            info.get("package_url") or f"https://pypi.org/project/{package}/",
            "PyPI JSON API",
            published=published,
            summary=info.get("summary"),
            metric=f"version {version}",
            score=45,
            tags=["python", "package"],
        ))
    return out


def collect_npm(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for package in source.get("packages", []):
        data = base.fetch_json(f"https://registry.npmjs.org/{urllib.parse.quote(package, safe='@/')}")
        latest = data.get("dist-tags", {}).get("latest")
        meta = data.get("versions", {}).get(latest, {}) if latest else {}
        out.append(base.item(
            "Coding & Developer Tools",
            f"npm package update: {package} {latest}",
            f"https://www.npmjs.com/package/{package}",
            "npm Registry API",
            published=data.get("time", {}).get(latest) if latest else None,
            summary=meta.get("description") or data.get("description"),
            metric=f"latest {latest}",
            score=45,
            tags=["javascript", "package"],
        ))
    return out


def collect_cisa_kev(source: dict[str, Any]) -> list[dict[str, Any]]:
    data = base.fetch_json(source.get("url", "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"))
    vulns = data.get("vulnerabilities", [])
    out: list[dict[str, Any]] = []
    for vuln in sorted(vulns, key=lambda x: base.parse_date(x.get("dateAdded")), reverse=True)[: int(source.get("limit", 8))]:
        out.append(base.item(
            "Coding & Developer Tools",
            f"CISA KEV: {vuln.get('cveID')} affecting {vuln.get('vendorProject')} {vuln.get('product')}",
            "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "CISA KEV JSON catalog",
            published=vuln.get("dateAdded"),
            summary=vuln.get("shortDescription"),
            metric=f"Due: {vuln.get('dueDate')}",
            score=85,
            tags=["security", "vulnerability"],
        ))
    return out


def collect_worldbank(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    country = source.get("country", "LK")
    for indicator in source.get("indicators", []):
        code = indicator.get("code")
        data = base.fetch_json(base.url(f"https://api.worldbank.org/v2/country/{country}/indicator/{code}", {"format": "json", "per_page": 5, "MRV": 5}))
        rows = data[1] if isinstance(data, list) and len(data) > 1 else []
        valid = [row for row in rows if row.get("value") is not None]
        if valid:
            row = valid[0]
            out.append(base.item(
                "Sri Lanka / CSE / Economy",
                f"World Bank indicator: {indicator.get('name', code)}",
                f"https://data.worldbank.org/indicator/{code}?locations={country}",
                "World Bank Indicators API",
                published=row.get("date"),
                summary=f"Latest value: {row.get('value')} for {row.get('country', {}).get('value', country)}.",
                metric=f"{code} {row.get('date')}: {row.get('value')}",
                score=35,
                tags=["macro", "official-data"],
            ))
    return out


def collect_open_meteo(source: dict[str, Any]) -> list[dict[str, Any]]:
    data = base.fetch_json(base.url("https://api.open-meteo.com/v1/forecast", {
        "latitude": source.get("latitude", 6.9271), "longitude": source.get("longitude", 79.8612),
        "current": "temperature_2m,precipitation,wind_speed_10m", "timezone": source.get("timezone", "Asia/Colombo")
    }))
    current = data.get("current", {})
    units = data.get("current_units", {})
    summary = "; ".join([f"{k}: {v} {units.get(k, '')}" for k, v in current.items() if k != "time"])
    return [base.item(
        "Sri Lanka / CSE / Economy",
        f"Local operating context weather: {source.get('location', 'Colombo')}",
        "https://open-meteo.com/",
        "Open-Meteo API",
        published=current.get("time"),
        summary=summary,
        metric=source.get("location", "Colombo"),
        score=20,
        tags=["weather", "local-context"],
    )]


def collect_stooq(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sym in source.get("symbols", ["^spx", "^ndq", "xauusd"]):
        csv = base.fetch_text(base.url("https://stooq.com/q/l/", {"s": sym, "f": "sd2t2ohlcv", "h": "", "e": "csv"}))
        lines = [line.strip() for line in csv.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        row = dict(zip(lines[0].split(","), lines[1].split(",")))
        close = row.get("Close") or "n/a"
        out.append(base.item(
            "Global Markets",
            f"Market snapshot: {sym}",
            f"https://stooq.com/q/?s={urllib.parse.quote(sym)}",
            "Stooq quote endpoint",
            published=f"{row.get('Date')} {row.get('Time')}",
            summary=f"Open {row.get('Open')}, high {row.get('High')}, low {row.get('Low')}, close {close}, volume {row.get('Volume')}",
            metric=f"close {close}",
            score=35,
            tags=["market-data"],
        ))
    return out


def should_run(source: dict[str, Any], profile: str) -> bool:
    profiles = source.get("profiles", ["hourly", "daily"])
    return source.get("enabled", True) and (profile in profiles or "all" in profiles)


def collect(config: dict[str, Any], profile: str) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    collectors = {
        "hn": base.collect_hn,
        "arxiv": base.collect_arxiv,
        "github": base.collect_github,
        "gdelt": base.collect_gdelt,
        "fx": base.collect_fx,
        "coingecko": base.collect_coingecko,
        "github_releases": collect_github_releases,
        "github_advisories": collect_github_advisories,
        "devto": collect_devto,
        "stackexchange": collect_stackexchange,
        "rss": collect_rss,
        "pypi": collect_pypi,
        "npm": collect_npm,
        "cisa_kev": collect_cisa_kev,
        "worldbank": collect_worldbank,
        "open_meteo": collect_open_meteo,
        "stooq": collect_stooq,
    }
    items: list[dict[str, Any]] = []
    failures: list[str] = []
    diagnostics: dict[str, Any] = {}
    for source in config.get("sources", []):
        if not should_run(source, profile):
            continue
        fn = collectors.get(source.get("type"))
        if not fn:
            failures.append(f"{source.get('name')}: unsupported source type {source.get('type')}")
            continue
        got, failed, diag = base.safe(source.get("name", source.get("type")), lambda s=source, f=fn: f(s))
        items.extend(got)
        failures.extend(failed)
        diagnostics.update(diag)
        time.sleep(float(source.get("pause_seconds", 0.12)))
    return base.dedupe(items), failures, diagnostics


def render(label: str, kind: str, output_path: str, items: list[dict[str, Any]], failures: list[str], diagnostics: dict[str, Any], config: dict[str, Any]) -> str:
    human = "Hourly Update" if kind == "hourly" else "Intelligence Brief"
    lines = [f"# SignalDaily {human} {base.TITLE_DASH} {label}", "", "Generated by the high-volume API-powered SignalDaily pipeline. Educational only; not financial advice.", ""]
    lines += ["## Executive Summary", *base.exec_summary(items, failures), ""]
    for section in SECTIONS:
        lines.append(f"## {section}")
        rows = base.by_section(items, section)
        lines.extend([base.bullet(x) for x in rows] if rows else [base.fallback(section)])
        if section == "Sri Lanka / CSE / Economy":
            lines += ["", "Educational boundary: this section may discuss market context, but it does not recommend buying, selling, holding, or trading any security or asset."]
        lines.append("")
    lines += ["## Opportunity Radar", *base.opportunities(items), ""]
    lines += ["## Deep Dive of the Day", *base.deep_dive(items), ""]
    lines += ["## Watchlist for Next Run", "- Check official AI lab blogs, GitHub releases, package registries, and security advisories for primary confirmation.", "- Review CBSL, CSE, SEC Sri Lanka, and listed-company announcements before treating local-market items as complete.", "- Verify market data after the next market close; weekend or holiday data may be stale.", "- Watch repeated items across hourly updates and deduplicate manually in weekly recaps."]
    if failures:
        lines.append("- Fix or replace failed API sources listed in Automation Notes.")
    lines += ["", "## GitHub-Ready Output", f"1. Suggested file path: `{output_path}`", f"2. Suggested commit message: `automation: add SignalDaily {kind} update for {label}`", "3. Telegram-ready alert message:", "", "```text", f"SignalDaily {human} - {label}", f"Generated {len(items)} API-backed signals across AI, dev tools, Sri Lanka/CSE/economy, and global markets.", f"Full report: {output_path}", "Educational only; not financial advice.", "```", ""]
    lines += ["## Automation Notes", f"- Items collected: {len(items)}", f"- Source failures: {len(failures)}"]
    lines.extend([f"- Failure: {x}" for x in failures[:15]])
    lines.extend([f"- {name}: {data}" for name, data in sorted(diagnostics.items())])
    lines += ["", "## Sources", *(base.sources(items, config) or ["- SignalDaily source registry: config/hourly-sources.json"]), ""]
    return "\n".join(lines)


def write_pack(path: Path, label: str, kind: str, items: list[dict[str, Any]], failures: list[str], diagnostics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"label": label, "report_kind": kind, "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "item_count": len(items), "failures": failures, "diagnostics": diagnostics, "items": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate high-volume SignalDaily hourly or daily Markdown.")
    parser.add_argument("--date", default=date_colombo())
    parser.add_argument("--slot", default=slot_colombo())
    parser.add_argument("--kind", choices=["hourly", "daily"], default="hourly")
    parser.add_argument("--profile", choices=["hourly", "daily"], default="hourly")
    parser.add_argument("--config", default=str(ROOT / "config" / "hourly-sources.json"))
    parser.add_argument("--output")
    parser.add_argument("--source-pack")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{2}-[01]\d-[0-3]\d", args.date):
        raise SystemExit("--date must use YYYY-MM-DD format")
    if not re.fullmatch(r"20\d{2}-[01]\d-[0-3]\d-[0-2]\d[0-5]\d", args.slot):
        raise SystemExit("--slot must use YYYY-MM-DD-HHMM format")
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    items, failures, diagnostics = collect(config, args.profile)
    if args.kind == "daily":
        output = Path(args.output or ROOT / "daily" / f"{args.date}.md")
        pack = Path(args.source_pack or ROOT / "source-packs" / f"{args.date}.json")
        label = args.date
    else:
        output = Path(args.output or ROOT / "updates" / f"{args.slot}.md")
        pack = Path(args.source_pack or ROOT / "source-packs" / f"{args.slot}.json")
        label = args.slot
    output_path = output.as_posix() if not output.is_absolute() else output.relative_to(ROOT).as_posix()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(label, args.kind, output_path, items, failures, diagnostics, config), encoding="utf-8")
    write_pack(pack, label, args.kind, items, failures, diagnostics)
    print(f"Wrote {output}")
    print(f"Wrote {pack}")
    print(f"Collected {len(items)} item(s), {len(failures)} failure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
