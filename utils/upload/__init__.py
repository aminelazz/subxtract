"""Robust upload function with granular exception handling."""

from datetime import datetime
import asyncio
import io
import time
from pathlib import Path
from urllib.parse import quote
from typing import Any, BinaryIO, Dict, Literal, cast

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
from requests_toolbelt.multipart.encoder import MultipartEncoder
from tqdm.auto import tqdm
from tqdm.utils import CallbackIOWrapper

from utils.logger import get_logger
from config import BUZZHEAVIER_URL, GOFILE_URL
from._types import (
    UploadProgressType,
    UploadProgressTypeDict,
    UploadResult,
    GofileUploadResultDict,
    GofileUploadResult,
    BuzzheavierUploadResultDict,
    BuzzheavierUploadResult
)

logger = get_logger(__name__)

class UploadProgress:
    """Class to track upload progress."""

    def __init__(
            self: "UploadProgress",
            file_path: Path | str,
            total_size: int,
            log_interval: float = 0.5,  # Log at most once every 0.5 seconds
        ) -> None:

        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.total_size = total_size
        self.log_interval = log_interval
        self._last_log_time = 0.0

        # Redirect tqdm's raw '\r' output to an in-memory buffer so it never pollutes stderr/bot.log
        self._null_buffer = io.StringIO()
        self.progress_bar = tqdm(
            total=total_size,
            file=self._null_buffer,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            ascii=False,
            desc=f"Uploading {self.file_name}",
        )

    def update(self, bytes_uploaded: int) -> None:
        """Update the progress bar with the number of bytes uploaded."""
        self.progress_bar.update(bytes_uploaded)
        now = time.monotonic()
        # Log progress at most once every `log_interval` seconds or when upload is complete
        if (now - self._last_log_time >= self.log_interval) or self.is_complete:
            self._last_log_time = now
            # Use tqdm's formatted bar string (logged with proper prefix & '\n')
            logger.info("%s", self.progress_bar)

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
        self._null_buffer.close()

class UploadError(Exception):
    """Custom base exception for upload failures."""
    pass


def _perform_http_upload(
    path: Path,
    http_method: str,
    upload_url: str,
    req_headers: Dict[str, Any],
    progress: UploadProgress,
) -> requests.Response:
    """Executes the synchronous streaming HTTP upload in a worker thread."""
    with open(path, "rb") as f:
        # Wrap the file object with a callback to update progress
        wrapped_file = cast(BinaryIO, CallbackIOWrapper(progress.update, f, "read"))
        if http_method == "PUT":
            response = requests.put(
                upload_url,
                headers=req_headers,
                data=wrapped_file,
                timeout=(15, 300),  # (15s connect timeout, 300s read timeout)
            )
        else:
            # Use MultipartEncoder for streaming multipart/form-data uploads
            m = MultipartEncoder(
                fields={"file": (path.name, wrapped_file, "application/octet-stream")},
            )
            req_headers["Content-Type"] = m.content_type

            response = requests.post(
                upload_url,
                headers=req_headers,
                data=m,
                timeout=(15, 300),
            )
        # Raise HTTPError for 4xx or 5xx status codes
        response.raise_for_status()
    return response


async def upload_file(
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

    logger.info("Starting upload of '%s' to %s", file_path, upload_dest)
    await message.edit(content=f"⏳ Uploading `{Path(file_path).name}` to {upload_dest}...")

    path = Path(file_path)
    req_headers = dict(headers) if headers else {}

    # 1. Validate destination
    if upload_dest not in ("BUZZHEAVIER", "GOFILE"):
        err_msg = f"❌ Invalid upload destination specified: **{upload_dest}**"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(
            success=False,
            error_message=err_msg,
            file_url=None
        )

    # 2. Filesystem checks
    try:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Target path is not a file: {path}")
        total_size = path.stat().st_size
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        err_msg = f"❌ Filesystem error accessing `{path}`: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except OSError as e:
        err_msg = f"❌ OS error accessing file `{path}`: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)

    # 3. Determine endpoint & HTTP method
    encoded_filename = quote(path.name)
    if upload_dest == "BUZZHEAVIER":
        upload_url = f"{BUZZHEAVIER_URL.rstrip('/')}/{encoded_filename}"
        http_method = "PUT"
    else:  # GOFILE
        upload_url = GOFILE_URL
        http_method = "POST"
    progress = UploadProgress(path, total_size)

    # 4. Perform the upload with try-except-finally
    try:
        response = await asyncio.to_thread(
            _perform_http_upload,
            path,
            http_method,
            upload_url,
            req_headers,
            progress,
        )

        # Close the progress bar after upload completes
        progress.close()

        #region ---- For GOFILE ----
        if upload_dest == "GOFILE":
            # Parse the JSON response and convert to typed structure
            gofile_data: GofileUploadResultDict = response.json()
            # Convert to typed response for better error handling
            typed_response_gofile: GofileUploadResult = GofileUploadResult.from_dict(gofile_data)

            # Check for success and presence of data
            if not typed_response_gofile.success or not typed_response_gofile.data:
                err_msg = f"❌ GOFILE upload failed: {typed_response_gofile.status if typed_response_gofile.status else 'Unknown'}"
                logger.error(err_msg)
                await message.edit(content=f"{err_msg}\nSkipping...")
                return UploadResult(success=False, error_message=err_msg, file_url=None)

            # Extract the download page URL from the typed response & log success
            file_url = typed_response_gofile.data.download_page
            success_msg = f"✅ Successfully uploaded `{Path(file_path).name}` to GOFILE:\n{file_url}"
            logger.info(success_msg)
            await message.edit(content=success_msg)
            return UploadResult(success=True, file_url=file_url)
        #endregion ---- For GOFILE ----

        #region ---- For BUZZHEAVIER ----
        # Parse the JSON response and convert to typed structure
        buzzheavier_data: BuzzheavierUploadResultDict = response.json()
        # Convert to typed response for better error handling
        typed_response_buzzheavier: BuzzheavierUploadResult = BuzzheavierUploadResult.from_dict(buzzheavier_data)

        # Check for success and presence of data
        if not typed_response_buzzheavier.success or not typed_response_buzzheavier.data:
            err_msg = f"❌ BUZZHEAVIER upload failed: {typed_response_buzzheavier.error if typed_response_buzzheavier.error else 'Unknown'}"
            logger.error(err_msg)
            await message.edit(content=f"{err_msg}\nSkipping...")
            return UploadResult(success=False, error_message=err_msg, file_url=None)

        # Extract the download page URL from the typed response & log success
        file_url = typed_response_buzzheavier.download_url
        success_msg = f"✅ Successfully uploaded `{Path(file_path).name}` to BUZZHEAVIER:\n{file_url}"
        logger.info(success_msg)
        await message.edit(content=success_msg)
        return UploadResult(success=True, file_url=file_url)
        #endregion ---- For BUZZHEAVIER ----

    except (InvalidURL, MissingSchema) as e:
        err_msg = f"❌ Malformed upload URL `{upload_url}`: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except Timeout as e:
        err_msg = f"❌ Upload timed out for `{path.name}` to **{upload_dest}**: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except ReqConnectionError as e:
        err_msg = f"❌ Network connection failed while uploading `{path.name}`: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        resp_text = e.response.text[:200] if e.response is not None else ""
        err_msg = f"❌ HTTP {status_code} error uploading `{path.name}` to **{upload_dest}**: {resp_text}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except RequestException as e:
        err_msg = f"❌ Unexpected requests error uploading `{path.name}`: {e}"
        logger.error(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    except Exception as e:
        err_msg = f"❌ Unexpected error occurred while uploading `{path.name}`: {e}"
        logger.exception(err_msg)
        await message.edit(content=f"{err_msg}\nSkipping...")
        return UploadResult(success=False, error_message=err_msg, file_url=None)
    finally:
        # Guarantees progress bar cleanly closes even if exceptions occur mid-upload
        progress.close()
        await asyncio.sleep(0.5)  # Allow time for progress bar to finalize before next output
