"""
Regression check: known proprietary/client CompIDs must not re-enter fixtures.

This is not a PII scanner. It only fails if listed tokens appear outside
this test file (the deny-list itself names the tokens).
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Known real-firm CompIDs / proprietary names that escaped anonymisation.
# Expand this list when another real identifier is confirmed. Do not add
# public MICs (e.g. XNAS) or already-synthetic placeholders (CLIENT_A).
KNOWN_PROPRIETARY_IDENTIFIERS = ("BARX",)

SKIP_DIR_NAMES = {".git", "__pycache__", ".venv", "venv"}
SKIP_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pyc", ".zip"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".jsonl", ".example"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix:
            continue
        yield path


class TestIdentifierHygiene(unittest.TestCase):
    def test_known_proprietary_identifiers_absent(self):
        hits = []
        for path in _iter_text_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in KNOWN_PROPRIETARY_IDENTIFIERS:
                if token in text:
                    rel = path.relative_to(ROOT).as_posix()
                    hits.append(f"{rel}: {token}")
        self.assertEqual(
            hits,
            [],
            "Known proprietary identifiers found (not a full PII scan):\n"
            + "\n".join(hits),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
