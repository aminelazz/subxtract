"""Aria2 service module for managing downloads via Aria2 RPC."""
import json
import time
import os
from pathlib import Path
from typing import Any, Generator, Iterator

import requests
import aria2p
from config import ARIA2_RPC_HOST, ARIA2_RPC_PORT, ARIA2_RPC_SECRET, DOWNLOAD_DIR
from utils.logger import get_logger
from ._types import DownloadStatus, Files

# Configure logging
logger = get_logger("aria2_service")

client = aria2p.Client(host=ARIA2_RPC_HOST,
                  port=int(ARIA2_RPC_PORT),
                  secret=ARIA2_RPC_SECRET)
api = aria2p.API(client)

def check_connection() -> bool:
    """Checks the connection to the Aria2 RPC server."""
    try:
        jsonreq = json.dumps(
            {
                "jsonrpc":"2.0",
                "id":"azert",
                "method":"aria2.getVersion",
                "params": [f"token:{ARIA2_RPC_SECRET}"]
            }
        )
        c = requests.post(f"{ARIA2_RPC_HOST}:{ARIA2_RPC_PORT}/jsonrpc", data=jsonreq, timeout=20)
        if c.status_code != 200:
            logger.error("Failed to connect to Aria2 RPC server: HTTP %d", c.status_code)
            return False
        logger.info("Successfully connected to Aria2 RPC server.")
        return True
    except Exception as e:
        logger.error("Failed to connect to Aria2 RPC server: %s", e)
        return False

def add_torrent(torrent_url: str) -> str:
    """Adds a torrent or magnet link to Aria2 for downloading."""
    # Make sure download directory exists
    os.makedirs(Path(DOWNLOAD_DIR), exist_ok=True)

    if torrent_url.startswith("magnet:"):
        download = api.add_magnet(torrent_url, options={"dir": DOWNLOAD_DIR})
    else:
        download = api.add_uris(uris=[torrent_url], options={"dir": DOWNLOAD_DIR})
    return download.gid

def get_status(gid: str) -> DownloadStatus:
    """Retrieves the status of a download by its GID."""
    task = api.get_download(gid)

    return {
        "name": task.name,
        "status": task.status,
        "progress": task.progress_string(),
        "dir": task.dir,
        "followed_by_ids": task.followed_by_ids,
        "speed": task.download_speed_string(human_readable=True),
        "seeders": str(task.num_seeders) if task.is_torrent else "N/A",
        "num_selected_files": len([f for f in task.files if f.selected]),
        "num_total_files": len(task.files),
        "downloaded_size": task.completed_length_string(human_readable=True),
        "total_size": task.total_length_string(human_readable=True),
        "total_size_bytes": task.total_length,
        "eta": task.eta_string(),
        "error": task.error_message,
        "is_complete": task.is_complete,
        "files": [
            Files(
                idx=f.index, 
                path=f.path, 
                size=f.length_string(human_readable=True)
            ) for f in task.files
        ]
    }

def get_files(gid: str) -> list[Files] | None:
    """Retrieves selected, fully downloaded Matroska files for a download GID."""
    try:
        task = api.get_download(gid)
        file_list: list[Files] = [
            Files(
                idx=file.index,
                path=file.path,
                size=file.length_string(human_readable=True),
            )
            for file in task.files
            if file.selected
            and file.path.is_file()
            and file.path.suffix.lower() in [".mkv", ".mk3d", ".mka"]
        ]

        file_list.sort(key=lambda f: str(f.path))
    except Exception as e:
        logger.error("Error retrieving files for GID %s: %s", gid, e)
        return None
    return file_list

def pause_download(gid: str) -> bool:
    """Pauses an aria2 download."""
    try:
        api.get_download(gid).pause()

        while True:
            download = api.get_download(gid)
            if download.status == "paused":
                break
        logger.info("Download with GID %s has been paused.", gid)
        return True
    except Exception as e:
        logger.error("Error pausing download with GID %s: %s", gid, e)
        return False

def resume_download(gid: str) -> bool:
    """Resumes an aria2 download."""
    try:
        api.get_download(gid).resume()

        while True:
            download = api.get_download(gid)
            if download.status in {"active", "waiting", "complete"}:
                break
        logger.info("Download with GID %s has resumed.", gid)
        return True
    except Exception as e:
        logger.error("Error resuming download with GID %s: %s", gid, e)
        return False

def track_progress(gid: str) -> Iterator[DownloadStatus]:
    """Tracks the progress of a download by its GID."""
    download = get_status(gid)
    while not download["is_complete"]:
        download = get_status(gid)
        yield download

def wait_for_completion(gid: str) -> Path:
    """Waits for a download to complete and returns the download directory."""
    download = api.get_download(gid)
    while not download.is_complete:
        download = api.get_download(gid)
    return download.dir

def remove_download(gid: str, force: bool = False) -> bool:
    """Removes a download by its GID."""
    download = api.get_download(gid)
    if force:
        return download.remove(force=True)
    else:
        return download.remove()

def remove_all_downloads(force: bool = False) -> bool:
    """Removes all downloads."""
    downloads = api.get_downloads()
    for download in downloads:
        if force:
            return download.remove(force=True)
        else:
            return download.remove()
    time.sleep(1)  # Give some time for Aria2 to process removals
    return True
