"""Type definitions for the aria2 service."""

from typing import TypedDict
from pathlib import Path

class FilesDict(TypedDict):
    """Describe a file included in a download."""
    index: int
    path: Path
    size: str

class DownloadStatus(TypedDict):
    """Describe the current status of a download."""
    name: str
    status: str
    progress: str
    dir: Path
    followed_by_ids: list[str] | None
    speed: str
    seeders: str
    num_selected_files: int
    num_total_files: int
    downloaded_size: str
    total_size: str
    total_size_bytes: int
    eta: str
    error: str | None
    is_complete: bool
    files: list[FilesDict]
