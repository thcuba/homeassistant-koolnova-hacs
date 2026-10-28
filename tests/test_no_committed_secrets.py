"""No credential may be committed to this repository.

An earlier tests/ directory shipped a plaintext account and had to be purged from history in v1.2.6;
six exploration scripts kept another one until this guard was added. The check is deliberately
narrow: it looks for the shapes this repo has actually leaked (a hardcoded password assignment and a
real-looking email literal), not for entropy, so it stays readable and does not fire on fixtures.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCANNED_SUFFIXES = {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".sh"}

# A password/secret assigned to a non-empty string literal.
SECRET_ASSIGNMENT = re.compile(
    r"""^\s*[\w.]*(?:password|passwd|secret|token|api_key|apikey)[\w.]*\s*[=:]\s*['"][^'"\s]{3,}['"]""",
    re.IGNORECASE | re.MULTILINE,
)

# An email literal, except the reserved/example forms and the project's own no-reply identity.
EMAIL = re.compile(r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "users.noreply.github.com")
# The project's public contact address (CODE_OF_CONDUCT), published on purpose by its author.
ALLOWED_EMAILS = {"user@example.com", "luisgsluis@gmail.com"}
# An asset name matches the shape of an address: icon@2x.png, logo@3x.jpg.
ASSET_NAME = re.compile(r"@\dx\.(?:png|jpe?g|svg|webp|gif|ico)$", re.IGNORECASE)
# Placeholders that are obviously not credentials.
ALLOWED_VALUES = re.compile(
    r"""['"](?:\*\*\*|xxx+|your[_-]?\w*|placeholder|<[^>]+>|\$\{[^}]+\}|\{\{[^}]+\}\})['"]""",
    re.IGNORECASE,
)


class TestNoCommittedSecrets(unittest.TestCase):
    def _scanned_files(self):
        for path in ROOT.rglob("*"):
            if ".git/" in str(path) or not path.is_file():
                continue
            if path.suffix.lower() in SCANNED_SUFFIXES:
                yield path

    def test_git_directory_is_not_scanned(self):
        """Sanity: the walker must skip .git, or every object file would be noise."""
        paths = [str(p) for p in self._scanned_files()]
        assert paths, "la scansione non ha trovato file"
        assert not any("/.git/" in p for p in paths)

    def test_no_hardcoded_password(self):
        offenders = []
        for path in self._scanned_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for match in SECRET_ASSIGNMENT.finditer(text):
                line = match.group(0)
                if ALLOWED_VALUES.search(line):
                    continue
                offenders.append(f"{path.relative_to(ROOT)}: {line.strip()}")
        assert not offenders, "credenziali in chiaro committate:\n" + "\n".join(offenders)

    def test_no_real_email_address(self):
        offenders = []
        for path in self._scanned_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for match in EMAIL.finditer(text):
                address = match.group(0)
                if address in ALLOWED_EMAILS:
                    continue
                if address.lower().endswith(ALLOWED_EMAIL_DOMAINS):
                    continue
                if ASSET_NAME.search(address):
                    continue
                offenders.append(f"{path.relative_to(ROOT)}: {address}")
        assert not offenders, "indirizzi email reali nel repo:\n" + "\n".join(offenders)


if __name__ == "__main__":
    unittest.main()
