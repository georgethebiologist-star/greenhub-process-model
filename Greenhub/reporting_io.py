"""Atomic workbook output helpers for Windows-safe report replacement."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import time
from typing import Iterator
from uuid import uuid4

import pandas as pd


def _temporary_workbook_path(path: Path) -> Path:
    return path.with_name(f".{path.stem}.{uuid4().hex}.tmp{path.suffix}")


def _replace_with_retry(source: Path, destination: Path) -> None:
    last_error: OSError | None = None
    for attempt in range(5):
        try:
            os.replace(source, destination)
            return
        except OSError as error:
            last_error = error
            if attempt < 4:
                time.sleep(0.2 * (attempt + 1))
    if last_error is not None:
        raise last_error


def _remove_temporary(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


@contextmanager
def atomic_excel_writer(
    path: Path,
    *,
    engine: str = "openpyxl",
) -> Iterator[pd.ExcelWriter]:
    """Yield a writer and replace the destination only after a complete workbook."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_workbook_path(destination)
    try:
        with pd.ExcelWriter(temporary, engine=engine) as writer:
            yield writer
        _replace_with_retry(temporary, destination)
    except Exception:
        _remove_temporary(temporary)
        raise


def atomic_save_workbook(workbook: object, path: Path) -> None:
    """Save an openpyxl-compatible workbook without rewriting in place."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_workbook_path(destination)
    try:
        workbook.save(temporary)
        _replace_with_retry(temporary, destination)
    except Exception:
        _remove_temporary(temporary)
        raise
