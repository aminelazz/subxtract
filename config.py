"""Configuration module for the Discord bot and Aria2 integration."""

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ARIA2_RPC_URL = os.getenv("ARIA2_RPC_URL", "http://localhost:6800/jsonrpc")
ARIA2_RPC_HOST = os.getenv("ARIA2_RPC_HOST", "http://localhost")
ARIA2_RPC_PORT = os.getenv("ARIA2_RPC_PORT", "6800")
ARIA2_RPC_SECRET = os.getenv("ARIA2_RPC_SECRET", "")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./temp/downloads")
EXTRACT_DIR = os.getenv("EXTRACT_DIR", "./temp/extracted")
SCHEMAS_DIR = os.getenv("SCHEMAS_DIR", "./schemas")
ALLOWED_CHANNELS_FILE = os.getenv("ALLOWED_CHANNELS_FILE", "./data/allowed_channels.json")
CURRENT_DL_FILE = os.getenv("CURRENT_DL_FILE", "./data/current_download.json")
QUEUE_FILE = os.getenv("QUEUE_FILE", "./data/queue.json")
