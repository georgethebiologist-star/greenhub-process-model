"""Generate the project-neutral Phase 3–7 dataset/input reuse catalogs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from biorefinery_platform.data_catalog import write_catalog_bundle


if __name__ == "__main__":
    manifest = write_catalog_bundle()
    print(manifest["counts"])
