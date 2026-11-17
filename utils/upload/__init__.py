"""Robust upload function with granular exception handling."""

from pathlib import Path
from urllib.parse import quote
from typing import Any, BinaryIO, Dict, Generator, Literal
import os

from interactions import Message
import requests
from requests.exceptions import (
    ConnectionError as ReqConnectionError,
    HTTPError,
    InvalidURL,
    MissingSchema,
    RequestException,
    Timeout,
)
from tqdm.auto import tqdm

from utils.logger import get_logger
from config import BUZZHEAVIER_URL, GOFILE_URL
from._types import UploadProgressType, UploadProgressTypeDict, UploadResult, GofileUploadResultDict, GofileUploadResult

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

class UploadError(Exception):
    """Custom base exception for upload failures."""
    pass

def upload_file(
        message: Message,
        file_path: Path | str,
        upload_dest: Literal["BUZZHEAVIER", "GOFILE"],
        headers: Dict[str, Any] | None = None,
        chunk_size: int = 64 * 1024,  # 64 KB is optimal for socket throughput
    ) -> UploadResult:
    """
    Uploads a file to the specified destination with streaming progress tracking
    and comprehensive exception handling.
    Args:
        message (Message): Discord message object for status updates.
        file_path (Path | str): Path to the file to upload.
        upload_dest (Literal["BUZZHEAVIER", "GOFILE"]): Target upload host.
        headers (Dict[str, Any] | None): Optional HTTP headers.
        chunk_size (int): Size of chunks in bytes (defaults to 64 KB).
    Returns:
        UploadResult: The result of the upload.
    """
    
    path = Path(file_path)

    # 1. Validate destination
    if upload_dest not in ("BUZZHEAVIER", "GOFILE"):
        logger.error("Invalid upload destination specified: '%s'", upload_dest)
        return UploadResult(success=False, file_url=None)

    # 2. Filesystem checks
    try:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Target path is not a file: {path}")
        total_size = path.stat().st_size
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        logger.error("Filesystem error reading '%s': %s", path, e)
        return UploadResult(success=False, file_url=None)
    except OSError as e:
        logger.error("OS error accessing file '%s': %s", path, e)
        return UploadResult(success=False, file_url=None)

    # 3. Determine endpoint & HTTP method
    encoded_filename = quote(path.name)
    if upload_dest == "BUZZHEAVIER":
        upload_url = f"{BUZZHEAVIER_URL.rstrip('/')}/{encoded_filename}"
        http_method = "PUT"
    else:  # GOFILE
        upload_url = GOFILE_URL
        http_method = "POST"
    progress = UploadProgress(path, total_size)

    # Generator that streams chunks to requests while updating progress
    def stream_file_with_progress(file_obj: BinaryIO) -> Generator[bytes, None, None]:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            progress.update(len(chunk))
            yield chunk

    # 4. Perform the upload with try-except-finally
    try:
        with open(path, "rb") as f:
            stream_data = stream_file_with_progress(f)
            if http_method == "PUT":
                response = requests.put(
                    upload_url,
                    headers=headers,
                    data=stream_data,
                    timeout=(15, 300),  # (15s connect timeout, 300s read timeout)
                )
            else:
                response = requests.post(
                    upload_url,
                    headers=headers,
                    data=stream_data,
                    timeout=(15, 300),
                )
            # Raise HTTPError for 4xx or 5xx status codes
            response.raise_for_status()
        
        # For GOFILE
        if upload_dest == "GOFILE":
            # Parse the JSON response and convert to typed structure
            data: GofileUploadResultDict = response.json()
            # Convert to typed response for better error handling
            typed_response: GofileUploadResult = GofileUploadResult.from_dict(data)

            # Check for success and presence of data
            if not typed_response.success or not typed_response.data:
                logger.error("GOFILE upload failed: %s", typed_response.status if typed_response.status else "Unknown")
                return UploadResult(success=False, file_url=None)

            # Extract the download page URL from the typed response & log success
            file_url = typed_response.data.download_page
            logger.info("Successfully uploaded '%s' to GOFILE: %s", path.name, file_url)
            return UploadResult(success=True, file_url=file_url)
        # For BUZZHEAVIER
        else:
            logger.info("Successfully uploaded '%s' to BUZZHEAVIER: %s", path.name, upload_url)
            return UploadResult(success=True, file_url=upload_url)

    except (InvalidURL, MissingSchema) as e:
        logger.error("Malformed upload URL '%s': %s", upload_url, e)
        return UploadResult(success=False, file_url=None)
    except Timeout as e:
        logger.error("Upload timed out for '%s' to %s: %s", path.name, upload_dest, e)
        return UploadResult(success=False, file_url=None)
    except ReqConnectionError as e:
        logger.error("Network connection failed while uploading '%s': %s", path.name, e)
        return UploadResult(success=False, file_url=None)
    except HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        resp_text = e.response.text[:200] if e.response is not None else ""
        logger.error(
            "HTTP %s error uploading '%s' to %s: %s",
            status_code,
            path.name,
            upload_dest,
            resp_text,
        )
        return UploadResult(success=False, file_url=None)
    except RequestException as e:
        logger.error("Unexpected requests error uploading '%s': %s", path.name, e)
        return UploadResult(success=False, file_url=None)
    except Exception as e:
        logger.exception("Unexpected error occurred while uploading '%s': %s", path.name, e)
        return UploadResult(success=False, file_url=None)
    finally:
        # Guarantees progress bar cleanly closes even if exceptions occur mid-upload
        progress.close()
