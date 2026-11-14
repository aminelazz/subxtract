"""File utilities module for handling file operations."""

import os
from pathlib import Path
import shutil
import json

from config import TEMP_DIR, EXTRACT_DIR, DOWNLOAD_DIR
from config import ALLOWED_CHANNELS_FILE, CURRENT_DL_FILE, QUEUE_FILE
from utils.logger import get_logger
from ._types import AllowedChannelsTypeDict, CurrentDLObjectDict, AllowedChannelsType, GuildObject, CurrentDLObject, QueueItem, QueueObject, QueueObjectDict

DISCORD_MAX_FILE_SIZE = 20 * 1024 * 1024

def clear_temp(path: Path = Path(TEMP_DIR)):
    """Clears the temporary directory."""
    if path.exists():
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

def get_temp_files(path: Path) -> dict[str, list[str]] | None:
    """
    Retrieves a list of all file paths within a given directory and its subdirectories.

    Args:
        path (Path): The path to the starting directory.

    Returns:
        dict | None: A dictionary containing full paths and relative filenames of the files found,
                      or None if the path does not exist.
    """
    file_list: list[str] = []
    if not path.exists():
        return None

    for root, _dirs, files in os.walk(path):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_list.append(full_path)

    # Remove all files except matroska files
    file_list = [f for f in file_list if f.lower().endswith((".mkv", ".mk3d", ".mka"))]
    file_list.sort()

    # Return a dict containing file with full paths & relative paths
    return {
        "full_paths": file_list,
        "filenames": [os.path.relpath(f, path) for f in file_list]
    }

def clear_download_dir(path: Path = Path(DOWNLOAD_DIR)):
    """Clears all files and subdirectories in the specified download directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

def clear_extract_dir(path: Path = Path(EXTRACT_DIR)):
    """Clears all files and subdirectories in the specified extract directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

def clear_directory(path: Path):
    """Clears all files and subdirectories in the specified directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

def save_file_to_extract_dir(content: bytes, filename: str):
    """Saves content to a file in the extract directory."""
    filepath = Path(EXTRACT_DIR) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath

def save_current_dl(gid="", user_id="", guild_id="", file_path: Path = Path(CURRENT_DL_FILE)):
    """Saves the current download GID to a file."""
    data: CurrentDLObject = CurrentDLObject(
        gid=gid,
        user_id=user_id,
        guild_id=guild_id
    )

    os.makedirs(file_path.parent, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data.to_dict(), f, ensure_ascii=False, indent=4)

def load_current_dl(file_path: Path = Path(CURRENT_DL_FILE)) -> CurrentDLObject | None:
    """Loads the current download GID from a file."""
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data: CurrentDLObjectDict = json.load(f)
    return CurrentDLObject.from_dict(data)

def clear_current_dl(file_path: Path = Path(CURRENT_DL_FILE)):
    """Clears the current download file."""
    if os.path.exists(file_path):
        os.remove(file_path)

def load_allowed_channels(file_path: Path = Path(ALLOWED_CHANNELS_FILE)) -> AllowedChannelsType | None:
    """Loads the content of allowed channel IDs from a file."""
    try:
        if not file_path.exists():
            return None
        data: AllowedChannelsTypeDict = {}

        with open(file_path, "r", encoding="utf-8") as f:
            data: AllowedChannelsTypeDict = json.load(f)
        return AllowedChannelsType.from_dict(data)
    except (json.JSONDecodeError, TypeError):
        return None
    except Exception:
        return None

def save_allowed_channels(guild_id: str, channel_id: str, file_path: Path = Path(ALLOWED_CHANNELS_FILE)):
    """Saves the content of allowed channel IDs to a file."""
    data = load_allowed_channels(file_path)
    if data is None:
        data = AllowedChannelsType(allowed_channels=[])

    # Check if the guild already exists
    guild = next((g for g in data.allowed_channels if g.guild == guild_id), None)
    if guild is None:
        # If not, create a new guild entry
        guild = GuildObject(guild=guild_id, channels=[channel_id])
        data.allowed_channels.append(guild)

    # Add the channel ID if it's not already in the list
    if channel_id not in guild.channels:
        guild.channels.append(channel_id)

    # Save the updated data back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data.to_dict(), f, ensure_ascii=False, indent=4)

def remove_allowed_channel(guild_id: str, channel_id: str, file_path: Path = Path(ALLOWED_CHANNELS_FILE)):
    """Removes a channel ID from the allowed channels file."""
    data = load_allowed_channels(file_path)
    if data is None:
        return

    # Find the guild entry
    guild = next((g for g in data.allowed_channels if g.guild == guild_id), None)
    if guild is not None:
        # Remove the channel ID if it exists
        if channel_id in guild.channels:
            guild.channels.remove(channel_id)

        # If the guild has no more channels, remove the guild entry
        if not guild.channels:
            data.allowed_channels.remove(guild)

        # Save the updated data back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, ensure_ascii=False, indent=4)

def load_queue(file_path: Path = Path(QUEUE_FILE)) -> list[QueueObject] | None:
    """Loads the download queue from a file."""
    # Configure logging
    logger = get_logger("load_queue_utils")

    try:
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data: list[QueueObjectDict] = json.load(f)
        queue = [
            QueueObject.from_dict({
                "user_id": item.get("user_id", ""),
                "links": item.get("links", [])
            })
            for item in data
        ]
        # logger.info("Loaded queue data from %s: %s", str(file_path), str(queue))  # Debug log
        return queue
    except (json.JSONDecodeError, TypeError) as e:
        logger.error("Error loading queue: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error loading queue: %s", e)
        return None

def get_user_queue(user_id: str, file_path: Path = Path(QUEUE_FILE)) -> QueueObject | None:
    """Retrieves a user's queue from the download queue file."""
    data = load_queue(file_path)
    if data is None:
        return None

    # Find the user's queue
    user_queue = next((item for item in data if item.user_id == user_id), None)
    return user_queue

def save_queue(user_id: str, links: list[str] | list[QueueItem], file_path: Path = Path(QUEUE_FILE), extraction_type: str = "all_without_audio") -> int:
    """Saves the download queue to a file.
    
    Args:
        user_id: User ID
        links: List of links (can be strings for backward compatibility) or list of dicts with {link, type}
        file_path: Path to queue file
        extraction_type: Default extraction type if links are strings
    """
    # Configure logging
    logger = get_logger("save_queue_utils")

    # Convert links to new format if needed
    normalized_links: list[QueueItem] = []
    for link in links:
        if isinstance(link, str):
            normalized_links.append(QueueItem(link=link, type=extraction_type))
        elif isinstance(link, QueueItem):
            normalized_links.append(QueueItem(
                link=link.link,
                type=link.type if hasattr(link, 'type') else extraction_type
            ))

    # Load existing data
    existing_data = load_queue(file_path)

    # Update or create new entry
    if existing_data is None:
        # No existing data, create new entry
        data = [QueueObject.from_dict({
            "user_id": user_id,
            "links": normalized_links
        })]
        added = len(normalized_links)
        logger.info("Creating new queue file with user %s and %d links.", user_id, added)
    else:
        # Update existing data
        data = existing_data
        # Find the user's queue
        user_queue = next((item for item in data if item.user_id == user_id), None)
        # If not found, create a new user queue
        if user_queue is None:
            user_queue = QueueObject.from_dict({
                "user_id": user_id,
                "links": normalized_links
            })
            data.append(user_queue)
            added = len(normalized_links)
            logger.info("Adding new user %s to queue with %d links.", user_id, added)
        # If found, update the links (avoid duplicates)
        else:
            existing_link_urls = {item.link for item in user_queue.links_dict}
            new_items = [item for item in normalized_links if item.link not in existing_link_urls]
            new_links = user_queue.links_dict + new_items
            added = len(new_items)
            data = [item for item in data if item.user_id != user_id]  # Remove old entry
            user_queue = QueueObject.from_dict({
                "user_id": user_id,
                "links": new_links
            })
            data.append(user_queue)  # Add updated entry
            logger.info("Updating user %s queue with %d links.", user_id, added)
            # logger.info("Saving queue data to %s: %s", str(file_path), str(data))  # Debug log

    data = [item.to_dict() for item in data]  # Ensure all items are QueueObject

    # Save back to file
    os.makedirs(file_path.parent, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return added

def remove_from_queue(user_id: str, links: list[str], file_path: Path = Path(QUEUE_FILE)) -> int:
    """Removes a user's links from the download queue file."""
    difference = 0
    data = load_queue(file_path)
    if data is None:
        difference = 0
        return difference

    # Remove the user's links from their queue
    user_queue = next((item for item in data if item.user_id == user_id), None)
    if user_queue is not None:
        # Extract just the link URLs for comparison
        links_to_remove = set(links)
        new_links = [item for item in user_queue.links_dict if item.link not in links_to_remove]
        difference = len(user_queue.links_dict) - len(new_links)
        
        # If the user's queue is empty, remove it
        if not new_links:
            data.remove(user_queue)
            data = [item.to_dict() for item in data]  # Ensure all items are QueueObject
            # Save and return
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return difference

        # Update the user's queue in the data
        data = [item for item in data if item.user_id != user_id]  # Remove old entry
        user_queue = QueueObject.from_dict({
            "user_id": user_id,
            "links": new_links
        })  # Create updated entry
        data.append(user_queue)  # Add updated entry

    # Save the updated data back to the file
    data = [item.to_dict() for item in data]  # Ensure all items are QueueObject
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return difference

def clear_user_queue(user_id: str, file_path: Path = Path(QUEUE_FILE)):
    """Clears a user's queue from the download queue file."""
    data = load_queue(file_path)
    if data is None:
        return

    # Remove the user's queue
    data = [item.to_dict() for item in data if item.user_id != user_id]

    # Save the updated data back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_split_zip(zip_path: Path, part_size: int = DISCORD_MAX_FILE_SIZE) -> list[Path]:
    """Creates a split zip file from the specified zip file."""
    # Configure logging
    logger = get_logger("create_split_zip")

    if not zip_path.exists():
        logger.error("Zip file %s does not exist.", str(zip_path))
        return []

    zip_files = []
    with open(zip_path, "rb") as f:
        index = 0
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break
            part_filename = zip_path.with_name(f"{zip_path.stem}.part{index:03d}{zip_path.suffix}")
            with open(part_filename, "wb") as part_file:
                part_file.write(chunk)
            logger.info("Created split zip part: %s", str(part_filename))
            zip_files.append(part_filename)
            index += 1
    # Optionally, remove the original zip file after splitting
    # os.remove(zip_path)

    return zip_files
