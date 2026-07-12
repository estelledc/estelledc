#!/usr/bin/env python3
"""Check that the GitHub Profile README matches the public Hub contract."""

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

NAVIGATION = {
    "Hub": "https://estelledc.github.io/",
    "Work": "https://estelledc.github.io/work/",
    "About": "https://estelledc.github.io/about/",
    "Résumé": "https://estelledc.github.io/resume/",
    "GitHub": "https://github.com/estelledc",
}

CASE_STATUSES = {
    "quanzhiping": "Shipped · 已上线",
    "bj-pal": "Prototype · 原型验证",
    "xiaochai": "Prototype · Private source",
    "study": "Maintained · 持续维护",
}
SELECTED_CASES = set(CASE_STATUSES)
FIRST_SCREEN_PROOFS = {
    "全智评 · Shipped": "https://estelledc.github.io/work/quanzhiping/",
    "BJ-Pal · 47/100 限定评测": "https://estelledc.github.io/work/bj-pal/",
    "UIKit Lab · 2/2 UI Test": (
        "https://github.com/estelledc/UIKitLifecycleDemo/blob/main/"
        "UIKitLifecycleDemoUITests/UIKitLifecycleDemoUITests.swift"
    ),
}
PUBLIC_ARTIFACTS = {
    "HardwareDecoder": {
        "url": "https://github.com/estelledc/HardwareDecoder/tree/main/Tests/HardwareDecoderCoreTests",
        "passed": 12,
        "total": 12,
        "suite": "XCTest",
        "minimum_links": 1,
    },
    "UIKit Lifecycle Lab": {
        "url": (
            "https://github.com/estelledc/UIKitLifecycleDemo/blob/main/"
            "UIKitLifecycleDemoUITests/UIKitLifecycleDemoUITests.swift"
        ),
        "passed": 2,
        "total": 2,
        "suite": "UI Test",
        "minimum_links": 2,
    },
}


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

    for label, url in NAVIGATION.items():
        require(f"[{label}]({url})" in text, f"navigation link missing: {label}")

    require("English summary:" in text, "English summary missing")
    require("### Public systems" in text, "Public systems selection missing")
    require("### Learning & engineering systems" in text, "learning and engineering selection missing")
    require("Evidence before adjectives" in text, "status evidence legend missing")
    require("Three proofs:" in text, "first-screen proof line missing")
    require("Product Engineer / AI Application Engineer" in text, "target role is missing")
    for label, url in FIRST_SCREEN_PROOFS.items():
        require((label, url) in links, f"first-screen proof contract mismatch: {label} -> {url}")
    for principle in [
        "Systems over isolated screens",
        "Evidence over adjectives",
        "Explainability over hidden magic",
        "Feedback over decoration",
    ]:
        require(principle in text, f"decision principle missing: {principle}")

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
    require((HUB / "about" / "index.html").is_file(), "staged About route missing")
    require((HUB / "resume" / "index.html").is_file(), "staged Resume route missing")

    for label, contract in PUBLIC_ARTIFACTS.items():
        url = str(contract["url"])
        passed = int(contract["passed"])
        total = int(contract["total"])
        suite = str(contract["suite"])
        minimum_links = int(contract["minimum_links"])
        marker = f"Verified · {passed}/{total} {suite}"

        require(passed == total and total > 0, f"artifact must remain a bounded passing claim: {label}")
        require((label, url) in links, f"public artifact contract mismatch: {label} -> {url}")
        require(sum(link_url == url for _, link_url in links) >= minimum_links, f"artifact link count drift: {label}")
        require(f"`{marker}`" in text, f"public artifact evidence drift: {label} -> {marker}")
        parsed = urlparse(url)
        require(
            parsed.netloc == "github.com" and "/main/" in parsed.path,
            f"artifact is not a main-branch GitHub source link: {url}",
        )

    for stale_url in [
        "https://estelledc.github.io/HardwareDecoder/",
        "https://estelledc.github.io/UIKitLifecycleDemo/",
    ]:
        require(stale_url not in text, f"undeployed lab page remains linked: {stale_url}")

    require("KeepL 为共同作者" in text, "BJ-Pal co-author attribution missing")
    require("不披露私有源码和真实学生数据" in text, "Quanzhiping privacy boundary missing")
    require("脱敏案例" in text, "private-source evidence boundary missing")

    require("github.com/estelledc/quanzhiping" not in text.lower(), "private Quanzhiping source linked")
    require("github.com/estelledc/xiaochai" not in text.lower(), "private Xiaochai source linked")
    require(
        "shields.io" not in text and "![" not in text and "<img" not in text.lower(),
        "badge or image wall detected",
    )
    require(not re.search(r"<[^>]+>", text), "README must stay pure Markdown without raw HTML")

    unique_urls = {url for _, url in links}
    require(len(unique_urls) <= 11, f"profile link surface is too broad: {len(unique_urls)} unique URLs")
    require(len(text.splitlines()) <= 80, "profile has grown into a repository inventory")

    if live:
        check_live_links(unique_urls, timeout)

    print(
        "OK: profile contract; "
        f"{len(SELECTED_CASES)} selected Hub cases + {len(PUBLIC_ARTIFACTS)} public labs / "
        f"{len(unique_urls)} unique links / "
        "staged Work, About, and Resume routes present"
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
