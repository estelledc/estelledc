#!/usr/bin/env python3
"""Check that the GitHub Profile README matches the public Hub contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HUB = ROOT.parent / "estelledc.github.io"

NAVIGATION = {
    "Hub": "https://estelledc.github.io/",
    "Work": "https://estelledc.github.io/work/",
    "Résumé": "https://estelledc.github.io/resume/",
    "GitHub": "https://github.com/estelledc",
}

CASE_STATUSES = {
    "quanzhiping": "Shipped · 已上线",
    "bj-pal": "Prototype · 原型验证",
    "xiaochai": "Prototype · Private source",
    "study": "Maintained · 持续维护",
    "zero-to-ai": "Maintained · v2.0",
    "embodied-ai": "Maintained · v1.2",
}
SELECTED_CASES = set(CASE_STATUSES)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def markdown_links(markdown: str) -> list[tuple[str, str]]:
    return re.findall(r"(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)", markdown)


def case_slug(url: str) -> str | None:
    parsed = urlparse(url)
    match = re.fullmatch(r"/work/([^/]+)/", parsed.path)
    if parsed.netloc == "estelledc.github.io" and match:
        return match.group(1)
    return None


def check() -> None:
    require(README.is_file(), "README.md missing")
    require(HUB.is_dir(), "Hub checkout missing; cannot verify staged public routes")
    text = README.read_text(encoding="utf-8")
    links = markdown_links(text)

    for label, url in NAVIGATION.items():
        require(f"[{label}]({url})" in text, f"navigation link missing: {label}")

    require("English summary:" in text, "English summary missing")
    require("### Public systems" in text, "Public systems selection missing")
    require("### Learning systems" in text, "Learning systems selection missing")
    require("Evidence before adjectives" in text, "status evidence legend missing")

    linked_cases = {slug for _, url in links if (slug := case_slug(url))}
    require(linked_cases == SELECTED_CASES, f"selected Hub cases mismatch: {sorted(linked_cases)}")
    for slug, status in sorted(CASE_STATUSES.items()):
        route = HUB / "work" / slug / "index.html"
        require(route.is_file(), f"staged Hub case route missing: /work/{slug}/")
        case_page = route.read_text(encoding="utf-8")
        require(f"https://estelledc.github.io/work/{slug}/" in case_page, f"case canonical mismatch: {slug}")
        require(status in case_page, f"Hub status mismatch for {slug}: {status}")
        require(status in text, f"Profile status mismatch for {slug}: {status}")
    require((HUB / "work" / "index.html").is_file(), "staged Work index missing")
    require((HUB / "resume" / "index.html").is_file(), "staged Resume route missing")

    require("KeepL 为共同作者" in text, "BJ-Pal co-author attribution missing")
    require("不披露私有源码和真实学生数据" in text, "Quanzhiping privacy boundary missing")
    require("脱敏案例" in text, "private-source evidence boundary missing")

    require("github.com/estelledc/quanzhiping" not in text.lower(), "private Quanzhiping source linked")
    require("github.com/estelledc/xiaochai" not in text.lower(), "private Xiaochai source linked")
    require("shields.io" not in text and "![" not in text and "<img" not in text.lower(), "badge or image wall detected")
    require(not re.search(r"<[^>]+>", text), "README must stay pure Markdown without raw HTML")

    unique_urls = {url for _, url in links}
    require(len(unique_urls) <= 10, f"profile link surface is too broad: {len(unique_urls)} unique URLs")
    require(len(text.splitlines()) <= 80, "profile has grown into a repository inventory")

    print(
        "OK: profile contract; "
        f"{len(SELECTED_CASES)} selected Hub cases / {len(unique_urls)} unique links / "
        "staged Work and Resume routes present"
    )


if __name__ == "__main__":
    try:
        check()
    except (AssertionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
