"""The manifest version must agree with the release tag.

Rule under test (docs/RELEASE.md): *"Tag and ``manifest.json`` MUST be identical"*. It is not
cosmetic - HACS reads the manifest to decide whether an update is available, so a manifest left
behind while tags move on makes HACS offer the same update indefinitely.

This is the state the repo was actually in: manifest 2.0.4, releases up to 2.0.9, with no check
anywhere. These tests exercise ``scripts/check_version.py``, which the release workflow also runs.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_version  # noqa: E402  (path must be set before the import)

REAL_MANIFEST = REPO_ROOT / "custom_components" / "koolnova" / "manifest.json"


def _manifest_with(version: str) -> pathlib.Path:
    """A throwaway manifest declaring ``version``."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "manifest.json"
    tmp.write_text(json.dumps({"domain": "koolnova", "version": version}), encoding="utf-8")
    return tmp


class VersionParsingTest(unittest.TestCase):
    def test_normalise_strips_a_v_prefix(self):
        self.assertEqual(check_version.normalise("v2.0.9"), "2.0.9")
        self.assertEqual(check_version.normalise("2.0.9"), "2.0.9")
        self.assertEqual(check_version.normalise(" v2.0.9 "), "2.0.9")

    def test_release_parts_compare_numerically_not_as_text(self):
        # The bug that started this: 2.0.10 must sort after 2.0.9, not before.
        self.assertGreater(check_version.release_parts("2.0.10"), check_version.release_parts("2.0.9"))
        self.assertGreater(check_version.release_parts("2.0.9"), check_version.release_parts("2.0.4"))

    def test_release_parts_ignores_a_suffix(self):
        self.assertEqual(check_version.release_parts("2.0.9-beta"), check_version.release_parts("2.0.9"))

    def test_release_parts_rejects_a_version_without_numbers(self):
        with self.assertRaises(ValueError):
            check_version.release_parts("main")


class TagCheckTest(unittest.TestCase):
    def test_matching_tag_passes(self):
        self.assertEqual(check_version.main(["--tag", "2.0.9", "--manifest", str(_manifest_with("2.0.9"))]), 0)

    def test_matching_tag_passes_when_the_tag_has_a_v_prefix(self):
        self.assertEqual(check_version.main(["--tag", "v2.0.9", "--manifest", str(_manifest_with("2.0.9"))]), 0)

    def test_mismatched_tag_fails(self):
        """A tag pushed while the manifest says something else - how 2.0.5..2.0.9 went out."""
        self.assertEqual(check_version.main(["--tag", "2.0.9", "--manifest", str(_manifest_with("2.0.4"))]), 1)

    def test_missing_manifest_fails(self):
        self.assertEqual(check_version.main(["--tag", "2.0.9", "--manifest", "/nonexistent/manifest.json"]), 1)

    def test_manifest_without_a_version_fails(self):
        broken = pathlib.Path(tempfile.mkdtemp()) / "manifest.json"
        broken.write_text(json.dumps({"domain": "koolnova"}), encoding="utf-8")
        self.assertEqual(check_version.main(["--tag", "2.0.9", "--manifest", str(broken)]), 1)


class FloorCheckTest(unittest.TestCase):
    def test_manifest_behind_the_latest_release_fails(self):
        """The exact shape of the bug: manifest 2.0.4, latest release 2.0.9."""
        self.assertEqual(
            check_version.main(["--not-older-than", "2.0.9", "--manifest", str(_manifest_with("2.0.4"))]), 1
        )

    def test_manifest_equal_to_the_latest_release_passes(self):
        self.assertEqual(
            check_version.main(["--not-older-than", "2.0.9", "--manifest", str(_manifest_with("2.0.9"))]), 0
        )

    def test_manifest_ahead_of_the_latest_release_passes(self):
        """Bumping the manifest before tagging is the intended workflow."""
        self.assertEqual(
            check_version.main(["--not-older-than", "2.0.9", "--manifest", str(_manifest_with("2.1.0"))]), 0
        )


@unittest.skipIf(shutil.which("git") is None, "git non disponibile")
class RealRepositoryTest(unittest.TestCase):
    """Against the real repo: this is what would have caught the drift."""

    def test_real_manifest_is_readable(self):
        self.assertRegex(check_version.read_manifest_version(REAL_MANIFEST), r"^\d+\.\d+\.\d+")

    def test_real_manifest_is_not_behind_the_latest_tag(self):
        tags = subprocess.run(
            ["git", "tag", "--sort=-creatordate"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if tags.returncode != 0 or not tags.stdout.strip():
            self.skipTest("nessun tag nel repo")
        latest = tags.stdout.split()[0]
        result = check_version.main(["--not-older-than", latest, "--manifest", str(REAL_MANIFEST)])
        self.assertEqual(result, 0, f"il manifest e' piu' vecchio dell'ultimo tag ({latest})")

    def test_real_manifest_matches_the_tag_when_one_points_at_head(self):
        """On a tag build the two must be identical, not merely ordered."""
        described = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if described.returncode != 0:
            self.skipTest("HEAD non e' un tag")
        self.assertEqual(
            check_version.main(["--tag", described.stdout.strip(), "--manifest", str(REAL_MANIFEST)]), 0
        )


class ReleaseDocsTest(unittest.TestCase):
    def test_release_docs_state_the_rule(self):
        """The rule the checks enforce must stay documented."""
        text = (REPO_ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
        self.assertIn("MUST be identical", text)


if __name__ == "__main__":
    unittest.main()
