#!/usr/bin/env python3
"""Get the version from `custom_components/gpm/manifest.json`."""

import json
from pathlib import Path


def get_version() -> str | None:
    """Get the version."""

    with Path("custom_components/gpm/manifest.json").open() as manifest_file:
        manifest = json.load(manifest_file)
        return manifest.get("version")


if __name__ == "__main__":
    print(get_version())  # noqa: T201
