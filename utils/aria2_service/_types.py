"""Type definitions for the aria2 service."""

from typing import TypedDict, NamedTuple
from pathlib import Path

class Files(NamedTuple):
    """Describe a file included in a download."""
    idx: int
    """The index of the file in the download."""
    path: Path
    """The path of the file relative to the download root."""
    size: str
    """The size of the file in human-readable format."""

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
    files: list[Files]
