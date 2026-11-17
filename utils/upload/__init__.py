"""Upload utilities for the subxtract project."""

from pathlib import Path
from typing import Any, BinaryIO, Dict, Literal

import requests
from tqdm import tqdm
from._types import UploadProgressType, UploadProgressTypeDict
from utils.logger import get_logger
from config import BUZZHEAVIER_URL, GOFILE_URL

logger = get_logger(__name__)

class UploadProgress:
    """Class to track upload progress."""

    def __init__(
            self: "UploadProgress",
            file_path: Path | str,
            total_size: int
        ) -> None:

        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.total_size = total_size
        self.progress_bar = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"Uploading {self.file_name}:"
        )

    def update(self, bytes_uploaded: int) -> None:
        """Update the progress bar with the number of bytes uploaded."""
        self.progress_bar.update(bytes_uploaded)

    @property
    def uploaded_size(self) -> int:
        """Current uploaded size in bytes."""
        return self.progress_bar.n

    @property
    def speed(self) -> float:
        """Current speed in bytes per second."""
        return self.progress_bar.format_dict.get("rate") or 0.0

    @property
    def eta(self) -> float:
        """Estimated remaining time in seconds."""
        rate = self.speed
        if rate and self.total_size:
            return max(0.0, (self.total_size - self.uploaded_size) / rate)
        return 0.0

    @property
    def percentage(self) -> float:
        """Upload percentage (0.0 to 100.0)."""
        if self.total_size:
            return (self.uploaded_size / self.total_size) * 100.0
        return 0.0

    @property
    def is_complete(self) -> bool:
        """Check if the upload is complete."""
        return self.uploaded_size >= self.total_size

    def get_stats(self) -> UploadProgressType:
        """Returns a snapshot of raw values and formatted strings for programmatic use
        (e.g., Discord status)."""

        uploaded = self.uploaded_size
        total = self.total_size
        speed = self.speed
        eta = self.eta
        
        data: UploadProgressTypeDict = {
            "file_path": str(self.file_path),
            "file_name": self.file_name,
            "uploaded_size": self.uploaded_size,
            "total_size": self.total_size,
            "percentage": self.percentage,
            "speed": self.speed,
            "eta": self.eta,
            "is_complete": self.is_complete,
            # Formatted human-readable strings:
            "total_formatted": tqdm.format_sizeof(total, suffix="B", divisor=1024),
            "uploaded_formatted": tqdm.format_sizeof(uploaded, suffix="B", divisor=1024),
            "speed_formatted": f"{tqdm.format_sizeof(speed, suffix='B', divisor=1024)}/s" if speed else "0 B/s",
            "eta_formatted": tqdm.format_interval(eta) if eta else "00:00",
        }

        return UploadProgressType.from_dict(data)

    def close(self) -> None:
        """Close the progress bar."""
        self.progress_bar.close()

def upload_file(
        file_path: Path | str,
        upload_dest: Literal["BUZZHEAVIER", "GOFILE"],
        headers: Dict[str, Any] | None = None
    ) -> None:
    """
    Uploads a file to the specified URL with progress tracking.
    
    Args:
        file_path (Path | str): The path to the file to be uploaded.
        upload_dest (Literal["BUZZHEAVIER", "GOFILE"]): The destination for the upload.
        headers (Dict[str, Any] | None): Optional headers to include in the request.
        
    Raises:
        ValueError: If an invalid upload destination is specified.
        
    Returns:
        None
    """

    file_path = Path(file_path)
    total_size = file_path.stat().st_size

    progress = UploadProgress(file_path, total_size)

    with open(file_path, "rb") as f:
        def read_in_chunks(file_object: BinaryIO, chunk_size: int = 1024):
            """Generator to read a file in chunks."""
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield data

        # Determine the actual upload URL based on the provided literal
        if upload_dest == "BUZZHEAVIER":
            upload_url = BUZZHEAVIER_URL
        elif upload_dest == "GOFILE":
            upload_url = GOFILE_URL
        else:
            raise ValueError("Invalid upload URL specified.")
        
        # Upload the file in chunks and update the progress bar
        for chunk in read_in_chunks(f):
            response = requests.post(upload_url, headers=headers, data=chunk)
            response.raise_for_status()  # Raise an error for bad responses
            progress.update(len(chunk))

            # Get the current progress stats and log them
            progress_stats = progress.get_stats()

    progress.close()
