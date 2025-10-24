"""File utilities module for handling file operations."""

import os
from pathlib import Path
import shutil
import json

from config import EXTRACT_DIR, DOWNLOAD_DIR, ALLOWED_CHANNELS_FILE, CURRENT_DL_FILE, QUEUE_FILE
from utils.logger import get_logger
from utils import utils

# Configure logging
logger = get_logger("file_utils")

# Define return type for allowed channels
# will be like this: {"allowed_channels": [{"guild": guild_id, "channels": [channel_id1, channel_id2]}, ...]}
class AllowedChannelsType(dict):
    """Type definition for allowed channels data structure."""
    allowed_channels: list["GuildObject"]

    def __init__(self, **data):
        super().__init__(**data)
        self.allowed_channels = [GuildObject(**guild) for guild in data.get("allowed_channels", [])]

    def dict(self):
        """Converts the AllowedChannelsType to a dictionary."""
        return {
            "allowed_channels": [dict(guild) for guild in self.allowed_channels]
        }

class GuildObject(dict):
    """Type definition for guild object in allowed channels."""
    def __init__(self, **data):
        super().__init__(**data)
        self.guild = data.get("guild", "")
        self.channels = data.get("channels", [])

    guild: str
    channels: list[str]

class CurrentDLObject(dict):
    """Type definition for current download object."""
    def __init__(self, **data):
        super().__init__(**data)
        self.gid = data.get("gid", "")
        self.user_id = data.get("user_id", "")
        self.guild_id = data.get("guild_id", "")

    gid: str
    user_id: str
    guild_id: str

class QueueObject(dict):
    """Type definition for queue object."""
    def __init__(self, **data):
        super().__init__(**data)
        self.user_id = data.get("user_id", "")
        self.links = data.get("links", [])

    user_id: str
    links: list[str]

def clear_temp(path: Path = Path("./temp")):
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
    file_list = []
    if not path.exists():
        return None

    for root, dirs, files in os.walk(path):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_list.append(full_path)

    # Remove all files except matroska files
    file_list = [f for f in file_list if f.lower().endswith(('.mkv', '.mk3d', '.mka'))]
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
    data = {
        "gid": gid,
        "user_id": user_id,
        "guild_id": guild_id
    }

    os.makedirs(file_path.parent, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_current_dl(file_path: Path = Path(CURRENT_DL_FILE)) -> CurrentDLObject | None:
    """Loads the current download GID from a file."""
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CurrentDLObject(**data)

def clear_current_dl(file_path: Path = Path(CURRENT_DL_FILE)):
    """Clears the current download file."""
    if os.path.exists(file_path):
        os.remove(file_path)

def load_allowed_channels(file_path: Path = Path(ALLOWED_CHANNELS_FILE)) -> AllowedChannelsType | None:
    """Loads the content of allowed channel IDs from a file."""
    try:
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AllowedChannelsType(**data)
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
        json.dump(data.dict(), f, ensure_ascii=False, indent=4)

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
            json.dump(data.dict(), f, ensure_ascii=False, indent=4)

def load_queue(file_path: Path = Path(QUEUE_FILE)) -> list[QueueObject] | None:
    """Loads the download queue from a file."""
    try:
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [QueueObject(**item) for item in data]
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

def save_queue(user_id: str, links: list[str], file_path: Path = Path(QUEUE_FILE)) -> int:
    """Saves the download queue to a file."""
    # Load existing data
    existing_data = load_queue(file_path)

    # Update or create new entry
    if existing_data is None:
        # No existing data, create new entry
        data = [QueueObject(user_id=user_id, links=list(set(links)))]
        added = len(links)
        logger.info("Creating new queue file with user %s and %d links.", user_id, added)
    else:
        # Update existing data
        data = existing_data
        # Find the user's queue
        user_queue = next((item for item in data if item.user_id == user_id), None)
        # If not found, create a new user queue
        if user_queue is None:
            user_queue = QueueObject(user_id=user_id, links=list(set(links)))
            data.append(user_queue)
            added = len(links)
            logger.info("Adding new user %s to queue with %d links.", user_id, added)
        # If found, update the links
        else:
            new_links = list(set(user_queue.links + links))
            added = len(new_links) - len(user_queue.links)
            data = [item for item in data if item.user_id != user_id]  # Remove old entry
            user_queue = QueueObject(user_id=user_id, links=new_links) # Create updated entry
            data.append(user_queue)  # Add updated entry
            logger.info("Updating user %s queue with %d links.", user_id, added)

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
        new_links: list[str] = list(set(user_queue.links) - set(links))
        difference = len(user_queue.links) - len(new_links)
        # If the user's queue is empty, remove it
        if not new_links:
            data.remove(user_queue)

        # Update the user's queue in the data
        data = [item for item in data if item.user_id != user_id]  # Remove old entry
        user_queue = QueueObject(user_id=user_id, links=new_links) # Create updated entry
        data.append(user_queue)  # Add updated entry

    # Save the updated data back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return difference

def clear_user_queue(user_id: str, file_path: Path = Path(QUEUE_FILE)):
    """Clears a user's queue from the download queue file."""
    data = load_queue(file_path)
    if data is None:
        return

    # Remove the user's queue
    data = [item for item in data if item.user_id != user_id]

    # Save the updated data back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_split_zip(zip_path: Path, part_size: int = 10 * 1024 * 1024) -> list[Path]:
    """Creates a split zip file from the specified zip file."""
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
