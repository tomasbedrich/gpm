"""Tests for the GPM integration."""

import io
import zipfile

TESTING_VERSIONS = "v0.8.8", "v0.9.9", "v1.0.0", "v2.0.0beta2"
DEFAULT_VERSION = "v1.0.0"


def make_zip(entries: dict[str, str]) -> bytes:
    """Return bytes of a zip archive containing the given {path: content} entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, content in entries.items():
            zf.writestr(path, content)
    return buf.getvalue()
