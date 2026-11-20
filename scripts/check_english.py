#!/usr/bin/env python3
"""Reject non-English script in repository names and UTF-8 text files."""

from pathlib import Path
import sys

IGNORED = {".git", "__pycache__", ".venv", "venv", ".DS_Store"}


def forbidden_letters(value: str) -> bool:
    return any(character.isalpha() and not character.isascii() for character in value)


def check(root: Path) -> list[str]:
    failures: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        safe_name = str(relative).encode("ascii", "backslashreplace").decode("ascii")
        if forbidden_letters(str(relative)):
            failures.append(f"Non-English file or folder name: {safe_name}")
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"Non-text file requires explicit review: {safe_name}")
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if forbidden_letters(line):
                failures.append(f"Non-English script: {safe_name}:{line_number}")
    return failures


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    if not root.is_dir():
        print("Repository directory does not exist.", file=sys.stderr)
        return 2
    failures = check(root)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("English repository check passed: names and text contain no non-English script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
