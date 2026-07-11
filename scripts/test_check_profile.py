#!/usr/bin/env python3
"""Regression tests for the Profile README contract."""

from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_profile


class ProfileContractTests(unittest.TestCase):
    def test_offline_profile_contract_passes(self) -> None:
        with redirect_stdout(StringIO()):
            check_profile.check()

    def test_public_artifacts_are_main_branch_github_evidence(self) -> None:
        for contract in check_profile.PUBLIC_ARTIFACTS.values():
            url = str(contract["url"])
            self.assertTrue(url.startswith("https://github.com/estelledc/"))
            self.assertIn("/main/", url)
            self.assertEqual(contract["passed"], contract["total"])

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
