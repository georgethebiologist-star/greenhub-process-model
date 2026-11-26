"""Bounded, resumable JSONL report archives for large sensitivity runs."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Iterator


LEGACY_ARCHIVE_NAME = "all_endpoint_reports.jsonl.gz"
ARCHIVE_PREFIX = "all_endpoint_reports_"
MAX_RECORDS_PER_ARCHIVE = 250
MAX_ARCHIVE_BYTES = 95 * 1024 * 1024


def report_archives(run_dir: Path) -> list[Path]:
    """Return either the legacy single archive or the ordered bounded shards."""
    shards = sorted(run_dir.glob(f"{ARCHIVE_PREFIX}[0-9][0-9][0-9].jsonl.gz"))
    if shards:
        return shards
    legacy = run_dir / LEGACY_ARCHIVE_NAME
    return [legacy] if legacy.is_file() else []


def iter_report_records(run_dir: Path) -> Iterator[dict]:
    archives = report_archives(run_dir)
    if not archives:
        raise FileNotFoundError(f"No endpoint report archive found in {run_dir}")
    for archive in archives:
        with gzip.open(archive, "rt", encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


def write_report_manifest(run_dir: Path, record_count: int | None = None) -> dict:
    archives = report_archives(run_dir)
    status_path = run_dir / "run_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    if record_count is None:
        record_count = int(status.get("completed_count", 0) or 0)
    shards = []
    for path in archives:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        shards.append({"file": path.name, "size_bytes": path.stat().st_size,
                       "sha256": digest.hexdigest()})
    manifest = {"schema": "greenhub-sensitivity-report-archive-1.0",
                "record_count": record_count, "maximum_shard_size_bytes": MAX_ARCHIVE_BYTES,
                "shards": shards}
    (run_dir / "report_archive_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    if status_path.exists():
        status["report_archives"] = [
            {"file": item["file"], "size_bytes": item["size_bytes"]} for item in shards
        ]
        status["report_archive_limit_bytes"] = MAX_ARCHIVE_BYTES
        status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def write_report_records(
    run_dir: Path,
    records: Iterable[dict],
    *,
    records_per_archive: int = MAX_RECORDS_PER_ARCHIVE,
) -> list[Path]:
    """Write, validate, then replace a report set using gzip JSONL shards."""
    if records_per_archive < 1:
        raise ValueError("records_per_archive must be positive")
    run_dir.mkdir(parents=True, exist_ok=True)
    old_archives = set(run_dir.glob(f"{ARCHIVE_PREFIX}[0-9][0-9][0-9].jsonl.gz"))
    legacy = run_dir / LEGACY_ARCHIVE_NAME
    if legacy.exists():
        old_archives.add(legacy)

    staged_paths: list[Path] = []
    record_count = 0
    with tempfile.TemporaryDirectory(prefix=".endpoint_reports_", dir=run_dir) as temp_name:
        stage = Path(temp_name)
        archive_index = 0
        records_in_archive = 0
        stream = None
        try:
            for record in records:
                if stream is None:
                    archive_index += 1
                    records_in_archive = 0
                    name = f"{ARCHIVE_PREFIX}{archive_index:03d}.jsonl.gz"
                    staged = stage / name
                    stream = gzip.open(staged, "wt", encoding="utf-8", newline="")
                    staged_paths.append(staged)
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                records_in_archive += 1
                record_count += 1
                if records_in_archive >= records_per_archive:
                    stream.close()
                    stream = None
            if stream is not None:
                stream.close()
                stream = None
        finally:
            if stream is not None:
                stream.close()

        verified_count = 0
        for archive in staged_paths:
            if archive.stat().st_size >= MAX_ARCHIVE_BYTES:
                raise ValueError(f"Split archive still exceeds the 95 MiB limit: {archive.name}")
            with gzip.open(archive, "rt", encoding="utf-8") as stream:
                for line in stream:
                    json.loads(line)
                    verified_count += 1
        if verified_count != record_count:
            raise ValueError(f"Archive verification count mismatch: {verified_count} != {record_count}")
        if record_count == 0:
            raise ValueError("Refusing to replace an existing report archive with zero records")

        published: list[Path] = []
        for staged in staged_paths:
            target = run_dir / staged.name
            os.replace(staged, target)
            published.append(target)
        keep = set(published)
        for old in old_archives:
            if old not in keep and old.exists():
                old.unlink()
        return published


class ReportShardWriter:
    """Append JSONL rows to bounded gzip shards, rotating by record count."""

    def __init__(self, run_dir: Path, records_per_archive: int = MAX_RECORDS_PER_ARCHIVE):
        self.run_dir = run_dir
        self.records_per_archive = records_per_archive
        self.archives = report_archives(run_dir)
        if self.archives and self.archives[0].name == LEGACY_ARCHIVE_NAME:
            raise ValueError("Convert the legacy report archive to shards before resuming the run.")
        self.index = len(self.archives)
        self.stream = None
        self.current_path: Path | None = None
        self.current_count = 0
        if self.archives:
            self.current_path = self.archives[-1]
            with gzip.open(self.current_path, "rt", encoding="utf-8") as source:
                self.current_count = sum(1 for line in source if line.strip())
            if self.current_count < self.records_per_archive:
                self.stream = gzip.open(self.current_path, "at", encoding="utf-8", newline="")
            else:
                self.current_path = None

    def __enter__(self) -> "ReportShardWriter":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _open_next(self) -> None:
        self.index += 1
        self.current_path = self.run_dir / f"{ARCHIVE_PREFIX}{self.index:03d}.jsonl.gz"
        self.stream = gzip.open(self.current_path, "wt", encoding="utf-8", newline="")
        self.current_count = 0

    def write(self, line: str) -> None:
        if self.stream is None:
            self._open_next()
        self.stream.write(line)
        self.current_count += 1
        if self.current_count >= self.records_per_archive:
            self._close_current()

    def flush(self) -> None:
        if self.stream is not None:
            self.stream.flush()

    def _close_current(self) -> None:
        if self.stream is None:
            return
        self.stream.close()
        self.stream = None
        if self.current_path is not None and self.current_path.stat().st_size >= MAX_ARCHIVE_BYTES:
            raise ValueError(f"Generated endpoint report shard exceeds 95 MiB: {self.current_path.name}")

    def close(self) -> None:
        self._close_current()
