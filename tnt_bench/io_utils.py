"""Text I/O with explicit encodings.

Path.read_text()/write_text() without an encoding use the platform locale —
which silently wrote cp1252 artifacts and mojibake'd UTF-8 prompts on
Windows during the pilot. Everything goes through UTF-8 now; the reader
falls back to cp1252 so pre-fix artifacts stay loadable.
"""

from __future__ import annotations

from pathlib import Path


def read_text(path: Path | str) -> str:
    data = Path(path).read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def write_text(path: Path | str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")
