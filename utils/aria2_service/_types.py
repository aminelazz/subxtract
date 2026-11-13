"""Type definitions for the aria2 service."""

from typing import NamedTuple
from pathlib import Path

class Files(NamedTuple):
    """Describe a file included in a download."""
    idx: int
    """The index of the file in the download."""
    path: Path
    """The path of the file relative to the download root."""
    size: str
    """The size of the file in human-readable format."""

class DownloadStatus(NamedTuple):
    """Describe the current status of a download."""

    name: str
    """Return the name of the download.
    
    Name is the name of the file if single-file, first file's directory name if multi-file.

    Returns:
        The download name.
    """

    status: str
    """Return the status of the download.
    
    Returns:
        `active`, `waiting`, `paused`, `error`, `complete` or `removed`.
    """

    dir: Path
    """Directory to save files.
    
    Returns:
        The directory where the files are saved.
    """

    progress: str
    """Return the progress of the download.

    Returns:
        The progress as a percentage.
    """

    speed: str
    """Return the download speed as string.
    
    Returns:
        The download speed string.
    """

    seeders: str
    """Return the number of seeders aria2 has connected to.
    
    BitTorrent only.
    
    Returns:
        The numbers of seeders.
    """

    num_selected_files: int
    """Return the number of selected files in the download.
    
    Returns:
        The number of selected files.
    """

    num_total_files: int
    """Return the total number of files in the download.
    
    Returns:
        The total number of files.
    """

    downloaded_size: str
    """Return the human-readable downloaded size of the download.
    
    Returns:
        The downloaded size.
    """

    total_size: str
    """Return the human-readable total size of the download.
    
    Returns:
        The total size.
    """

    total_size_bytes: int
    """Return the total size of the download in bytes.
    
    Returns:
        The total size in bytes.
    """

    eta: str
    """Return the estimated time of arrival for the download.
    
    Returns:
        The estimated time of arrival.
    """

    is_complete: bool
    """Return whether the download is complete.
    
    Returns:
        True if the download is complete, False otherwise.
    """

    files: list[Files]
    """Return a list of files included in the download.
    
    Returns:
        A list of elements of type `Files`.
    """

    followed_by_ids: list[str] | None = None
    """Return a list of GIDs of downloads that are followed by this download.

    Returns:
        A list of GIDs of downloads that are followed by this download, or None if there are no followed downloads.
    """

    error: str | None = None
    """Return the error message if the download has an error.

    Returns:
        The error message, or None if there is no error.
    """
