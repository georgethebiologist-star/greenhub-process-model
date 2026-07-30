"""In-process feed-profile discovery and user-profile registration."""

from __future__ import annotations

from pathlib import Path
from threading import RLock

from Greenhub.feed_profiles import (
    FeedProfile,
    feed_profile_from_mapping,
    load_feed_profile_csv,
    load_workbook_feed_profiles,
)


class FeedProfileService:
    def __init__(self) -> None:
        self._profiles = {item.profile_id: item for item in load_workbook_feed_profiles()}
        self._lock = RLock()

    def list_profiles(self) -> tuple[dict[str, object], ...]:
        with self._lock:
            return tuple(self._profiles[key].metadata() for key in sorted(self._profiles))

    def get_profile(self, profile_id: str | None) -> FeedProfile:
        selected = profile_id or "workbook_default"
        with self._lock:
            try:
                return self._profiles[selected]
            except KeyError as error:
                raise KeyError(f"Unknown feed profile '{selected}'.") from error

    def register(self, profile: FeedProfile, *, replace: bool = False) -> FeedProfile:
        with self._lock:
            if profile.profile_id in self._profiles and not replace:
                raise ValueError(f"Feed profile '{profile.profile_id}' already exists.")
            self._profiles[profile.profile_id] = profile
        return profile

    def register_mapping(self, payload: dict[str, object], *, replace: bool = False) -> FeedProfile:
        return self.register(feed_profile_from_mapping(payload), replace=replace)

    def register_csv(
        self,
        path: Path,
        profile_id: str,
        *,
        normalized: bool = False,
        replace: bool = False,
    ) -> FeedProfile:
        return self.register(load_feed_profile_csv(path, profile_id, normalized=normalized), replace=replace)
