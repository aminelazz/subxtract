"""Aria2 service module for managing downloads via Aria2 RPC."""
import json
import time
import os
from pathlib import Path

import requests
import aria2p
from config import ARIA2_RPC_HOST, ARIA2_RPC_PORT, ARIA2_RPC_SECRET, DOWNLOAD_DIR
from utils.logger import get_logger

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
        c = requests.post("http://localhost:6800/jsonrpc", data=jsonreq, timeout=20)
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

def get_status(gid: str):
    """Retrieves the status of a download by its GID."""
    task = api.get_download(gid)
    return {
        "name": task.name,
        "status": task.status,
        "progress": task.progress_string(),
        "dir": task.dir,
        "followed_by_ids": task.followed_by_ids,
        "speed": task.download_speed_string()
    }

def track_progress(gid: str):
    """Tracks the progress of a download by its GID."""
    download = api.get_download(gid)
    while not download.is_complete:
        download = api.get_download(gid)
        yield {
            "name": download.name,
            "progress": download.progress_string(),
            "downloaded_size": download.completed_length_string(),
            "full_size": download.total_length_string(),
            "status": download.status,
            "speed": download.download_speed_string(),
            "seeders": download.num_seeders if isinstance(download, aria2p.BitTorrent) else "N/A",
            "num_files": len(download.files),
            "eta": download.eta_string(),
            "dir": download.dir,
            "error": download.error_message
        }

def wait_for_completion(gid: str):
    """Waits for a download to complete and returns the download directory."""
    download = api.get_download(gid)
    while not download.is_complete:
        download = api.get_download(gid)
    return download.dir

def remove_download(gid: str, force: bool = False):
    """Removes a download by its GID."""
    download = api.get_download(gid)
    if force:
        download.remove(force=True)
    else:
        download.remove()

def remove_all_downloads(force: bool = False):
    """Removes all downloads."""
    downloads = api.get_downloads()
    for download in downloads:
        if force:
            download.remove(force=True)
        else:
            download.remove()
    time.sleep(1)  # Give some time for Aria2 to process removals
