#!/usr/bin/env python3
"""Regression tests for the Profile README contract."""

from __future__ import annotations

import re
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_profile


class ProfileContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = check_profile.README.read_text(encoding="utf-8")

    def test_offline_profile_contract_passes(self) -> None:
        with redirect_stdout(StringIO()):
            check_profile.check()

    def test_public_evidence_contract_has_exact_four_items(self) -> None:
        self.assertEqual(
            set(check_profile.PUBLIC_EVIDENCE),
            {"TraceFetch", "BJ-Pal", "Tencent/WeKnora PR #1785", "web-plan-execute"},
        )
        for label, contract in check_profile.PUBLIC_EVIDENCE.items():
            self.assertIn(f"[{label}]({contract['url']})", self.text)
            self.assertIn(contract["marker"], self.text)

    def test_source_rc_and_release_boundaries_are_explicit(self) -> None:
        tracefetch = check_profile.PUBLIC_EVIDENCE["TraceFetch"]
        web_plan_execute = check_profile.PUBLIC_EVIDENCE["web-plan-execute"]
        self.assertEqual(tracefetch["url"], "https://github.com/estelledc/tracefetch")
        self.assertNotIn("/releases/", tracefetch["url"])
        self.assertIn("/releases/tag/v0.9.0-rc.1", web_plan_execute["url"])
        self.assertIn("当前仍是 RC", self.text)
        self.assertIn("不等于生产 SLA、规模化运行或真实用户效果", self.text)

    def test_weknora_merge_and_bj_pal_public_status_are_fixed(self) -> None:
        self.assertIn("Merged OSS contribution", self.text)
        self.assertIn("4 条回归用例", self.text)
        self.assertIn("v6.29 · Public source", self.text)

    def test_role_and_four_evidence_items_fit_on_the_first_screen(self) -> None:
        first_screen = "\n".join(self.text.splitlines()[:18])
        self.assertIn(check_profile.TAGLINE, first_screen)
        for label, contract in check_profile.PUBLIC_EVIDENCE.items():
            self.assertIn(label, first_screen)
            self.assertIn(contract["marker"], first_screen)

    def test_navigation_and_private_work_route_stay_narrow(self) -> None:
        self.assertIn(check_profile.NAVIGATION_LINE, self.text)
        self.assertNotIn("[Hub](", self.text)
        self.assertNotIn("[GitHub](", self.text)
        self.assertIn("私有项目与 iOS 经历统一由 Work 页面承载", self.text)
        lowered = self.text.lower()
        for private_url in check_profile.PRIVATE_REPO_URLS:
            self.assertNotIn(private_url, lowered)

    def test_readme_is_static_pure_markdown_with_three_principles(self) -> None:
        self.assertNotIn("![", self.text)
        self.assertIsNone(re.search(r"<[^>]+>", self.text))
        self.assertLessEqual(len(self.text.splitlines()), 55)
        how = self.text.split("## How I work", 1)[1]
        self.assertEqual(len(re.findall(r"^- ", how, flags=re.MULTILINE)), 3)

    def test_live_check_accepts_successful_or_partial_responses(self) -> None:
        with patch.object(check_profile, "probe_live_url", return_value=(206, "resolved")):
            with redirect_stdout(StringIO()):
                check_profile.check_live_links({"https://example.test/evidence"}, timeout=1)

    def test_live_check_reports_404_with_the_original_url(self) -> None:
        missing = "https://example.test/missing"
        with patch.object(check_profile, "probe_live_url", return_value=(404, missing)):
            with self.assertRaisesRegex(AssertionError, r"404 https://example\.test/missing"):
                check_profile.check_live_links({missing}, timeout=1)


if __name__ == "__main__":
    unittest.main()
