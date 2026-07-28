#!/usr/bin/env python3
"""Check that the GitHub Profile README matches the public evidence contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HUB = ROOT.parent / "estelledc.github.io"

TAGLINE = "AI Application Engineer · Reliable agents, RAG/evals · Web/iOS delivery"
NAVIGATION = (
    ("Work", "https://estelledc.github.io/work/"),
    ("Résumé", "https://estelledc.github.io/resume/"),
    ("About", "https://estelledc.github.io/about/"),
)
NAVIGATION_LINE = " · ".join(f"[{label}]({url})" for label, url in NAVIGATION)
HUB_ROUTES = {
    "Work": HUB / "work" / "index.html",
    "Résumé": HUB / "resume" / "index.html",
    "About": HUB / "about" / "index.html",
}
PUBLIC_EVIDENCE = {
    "TraceFetch": {
        "url": "https://github.com/estelledc/tracefetch",
        "marker": "v1.0 · Public source",
    },
    "BJ-Pal": {
        "url": "https://github.com/estelledc/bj-pal",
        "marker": "v6.29 · Public source · Co-authored with KeepL",
    },
    "Tencent/WeKnora PR #1785": {
        "url": "https://github.com/Tencent/WeKnora/pull/1785",
        "marker": "Merged OSS contribution",
    },
    "web-plan-execute": {
        "url": "https://github.com/estelledc/web-plan-execute/releases/tag/v0.9.0-rc.1",
        "marker": "0.9.0-rc.1 · Public RC",
    },
}
STALE_MARKERS = (
    "47/100",
    "2/2 UI Test",
    "Three proofs",
    "Product Systems Builder",
    "全智评",
    "HardwareDecoder",
    "UIKit Lifecycle Lab",
)
PRIVATE_REPO_URLS = (
    "github.com/estelledc/quanzhiping",
    "github.com/estelledc/xiaochai",
)
DECORATION_MARKERS = (
    "shields.io",
    "github-readme-stats",
    "github-readme-streak",
    "streak-stats",
    "github-profile-trophy",
    "visitor-badge",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def markdown_links(markdown: str) -> list[tuple[str, str]]:
    return re.findall(r"(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)", markdown)


def probe_live_url(url: str, timeout: float) -> tuple[int | None, str]:
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Range": "bytes=0-0",
            "User-Agent": "estelledc-profile-link-check/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read(1)
            return response.status, response.geturl()
    except HTTPError as exc:
        return exc.code, exc.geturl()
    except URLError as exc:
        return None, str(exc.reason)


def check_live_links(urls: set[str], timeout: float) -> None:
    failures = []
    for url in sorted(urls):
        status, detail = probe_live_url(url, timeout)
        if status is None or not 200 <= status < 400:
            failures.append(f"{status or 'NETWORK'} {url} ({detail})")
        else:
            print(f"LIVE {status}: {url}")
    require(not failures, "live URL check failed:\n- " + "\n- ".join(failures))


def check(*, live: bool = False, timeout: float = 10.0) -> None:
    require(README.is_file(), "README.md missing")
    require(HUB.is_dir(), "Hub checkout missing; cannot verify staged public routes")
    text = README.read_text(encoding="utf-8")
    links = markdown_links(text)
    unique_urls = {url for _, url in links}

    require(text.startswith("# Jason Xun\n"), "profile title drift")
    require(f"**{TAGLINE}**" in text, "AI application positioning drift")
    for phrase in ["可运行、可评测、可恢复", "工具边界", "失败语义", "证据回放", "人工责任"]:
        require(phrase in text, f"Chinese positioning missing: {phrase}")
    require(text.count("English summary:") == 1, "exactly one English summary is required")

    require(text.count(NAVIGATION_LINE) == 1, "navigation must be Work / Résumé / About only")
    require("[Hub](" not in text, "Hub navigation link must be removed")
    require("[GitHub](" not in text, "GitHub self-link must be removed")
    require("https://github.com/estelledc" not in unique_urls, "GitHub profile self-link remains")
    for label, route in HUB_ROUTES.items():
        require(route.is_file(), f"staged Hub route missing: {label}")

    require(text.count("## Selected evidence") == 1, "Selected evidence section missing")
    require(text.count("## How I work") == 1, "How I work section missing")
    selected = text.split("## Selected evidence", 1)[1].split("## How I work", 1)[0]
    require(len(re.findall(r"^- ", selected, flags=re.MULTILINE)) == 4, "exactly four evidence items required")
    for label, contract in PUBLIC_EVIDENCE.items():
        url = contract["url"]
        marker = contract["marker"]
        require((label, url) in links, f"public evidence link mismatch: {label} -> {url}")
        quoted_marker = chr(96) + marker + chr(96)
        require(quoted_marker in text, f"public evidence status mismatch: {label} -> {marker}")
    first_screen = "\n".join(text.splitlines()[:18])
    require(TAGLINE in first_screen, "AI application role must remain on the first screen")
    for label, contract in PUBLIC_EVIDENCE.items():
        require(label in first_screen, f"public evidence must remain on the first screen: {label}")
        require(
            contract["marker"] in first_screen,
            f"public evidence status must remain on the first screen: {label}",
        )

    require("Co-authored with KeepL" in text, "BJ-Pal KeepL attribution missing")
    require("4 条回归用例" in text, "WeKnora regression evidence missing")
    require("当前仍是 RC" in text, "web-plan-execute RC boundary missing")
    require(
        "Release、RC 与测试收据只证明对应版本和范围" in text,
        "release and test receipt boundary missing",
    )
    require(
        "不等于生产 SLA、规模化运行或真实用户效果" in text,
        "production and user-outcome boundary missing",
    )

    require(
        "产品案例、私有项目的脱敏证据与 iOS 经历统一由 Work 页面承载。" in text,
        "Work routing for product, private, and iOS evidence missing",
    )
    hub_urls = {url for url in unique_urls if urlparse(url).netloc == "estelledc.github.io"}
    require(hub_urls == {url for _, url in NAVIGATION}, "Profile must not deep-link fixed Hub cases")
    lowered = text.lower()
    for private_url in PRIVATE_REPO_URLS:
        require(private_url not in lowered, f"private repository linked: {private_url}")
    for marker in STALE_MARKERS:
        require(marker not in text, f"stale profile claim remains: {marker}")

    how = text.split("## How I work", 1)[1].strip()
    require(not re.search(r"^## ", how, flags=re.MULTILINE), "How I work must be the final section")
    require(len(re.findall(r"^- ", how, flags=re.MULTILINE)) == 3, "exactly three working principles required")
    for principle in ["失败关闭", "可重放评测", "诚实边界"]:
        require(f"**{principle}**" in how, f"working principle missing: {principle}")

    require("![" not in text, "README images are forbidden")
    require(not re.search(r"<[^>]+>", text), "README must stay pure Markdown without raw HTML")
    for marker in DECORATION_MARKERS:
        require(marker not in lowered, f"dynamic decoration is forbidden: {marker}")
    require(
        all(urlparse(url).netloc in {"github.com", "estelledc.github.io"} for url in unique_urls),
        "unexpected link host",
    )
    require(len(unique_urls) <= 10, f"profile link surface is too broad: {len(unique_urls)} unique URLs")
    require(len(text.splitlines()) <= 55, "profile has grown beyond 55 lines")

    if live:
        check_live_links(unique_urls, timeout)

    print(
        "OK: profile contract; "
        f"{len(PUBLIC_EVIDENCE)} public evidence items / {len(unique_urls)} unique links / "
        "pure Markdown / staged Work, Résumé, and About routes present"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="probe every public URL and fail on 4xx/5xx or network errors",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="per-URL timeout in seconds for --live (default: 10)",
    )
    args = parser.parse_args()
    try:
        require(args.timeout > 0, "--timeout must be positive")
        check(live=args.live, timeout=args.timeout)
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
