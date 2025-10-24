# Subxtract

A Discord bot for downloading and extracting content from MKV (Matroska) files. Subxtract automates the process of downloading media files via Aria2 and extracting subtitles, attachments, chapters, and metadata from MKV containers.

## Features

- **Download Management**: Download files using torrents, magnet links, or direct download links via Aria2
- **MKV Extraction**: Extract the following from MKV files:
  - Subtitles (SRT, ASS, SSA formats)
  - Attachments (fonts, images, etc.)
  - Chapters (XML format)
  - Media information and metadata
- **Queue System**: Manage multiple download requests with a per-user queue
- **Channel Permissions**: Restrict bot commands to specific Discord channels
- **Real-time Progress**: Track download progress with live status updates
- **Split File Support**: Automatically split large zip files to fit Discord's 10MB upload limit
- **Cancellation**: Stop ongoing downloads and extractions at any time

## Requirements

### External Dependencies

- **Aria2**: Download manager with RPC support
- **mkvmerge**: Part of MKVToolNix for MKV file information
- **mkvextract**: Part of MKVToolNix for extracting MKV contents
- **mediainfo**: Media file analysis tool

### Python Dependencies

- Python 3.10+
- discord-py-interactions 5.15.0
- aria2p 0.12.1
- python-dotenv 1.1.1
- jsonschema 4.25.1
- jsonschema-gentypes 2.12.0

## Installation

### 1. Install External Tools

#### Windows
Download and install:
- [Aria2](https://github.com/aria2/aria2/releases)
- [MKVToolNix](https://mkvtoolnix.download/downloads.html)
- [MediaInfo](https://mediaarea.net/en/MediaInfo/Download)

Ensure all tools are added to your system PATH.

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install aria2 mkvtoolnix mediainfo
```

#### macOS
```bash
brew install aria2 mkvtoolnix mediainfo
```

### 2. Clone the Repository
```bash
git clone <repository-url>
cd subxtract
```

### 3. Create Virtual Environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment

Rename `.env.example` file to `.env` and edit it:

```env
# Discord Bot Token (required)
DISCORD_TOKEN=your_discord_bot_token_here

# Aria2 RPC Configuration
ARIA2_RPC_URL=http://localhost:6800/jsonrpc
ARIA2_RPC_HOST=localhost
ARIA2_RPC_PORT=6800
ARIA2_RPC_SECRET=

# Directory Configuration
TEMP_DIR=./temp
DOWNLOAD_DIR=./temp/downloads
EXTRACT_DIR=./temp/extracted
SCHEMAS_DIR=./schemas

# Data Files
ALLOWED_CHANNELS_FILE=./data/allowed_channels.json
CURRENT_DL_FILE=./data/current_download.json
QUEUE_FILE=./data/queue.json
```

### 6. Start Aria2 RPC Server

```bash
# Basic command
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800

# With secret (recommended)
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --rpc-secret=your_secret_here

# With additional options
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 \
       --max-connection-per-server=16 --split=16 --min-split-size=1M

# Using aria2.conf file
aria2c --conf-path="./config/aria2.conf"
```

### 7. Create Required Directories

```bash
mkdir -p data schemas temp/downloads temp/extracted
```

## Usage

### Starting the Bot

```bash
python bot.py
```

### Discord Commands

#### Setup Commands (Admin)
- `/allow_channel` - Allow bot commands in the current channel
- `/disallow_channel` - Disallow bot commands in the current channel

#### Download & Extraction
- `/extract <url>` - Download and extract content from MKV file(s)
  - Supports: Torrent files, magnet links, direct download URLs

#### Queue Management
- `/queue` - View your current download queue
- `/add_to_queue <url>` - Add a URL to your download queue
- `/remove_from_queue <url>` - Remove a URL from your queue
- `/clear_queue` - Clear your entire queue
- `/start_queue` - Process all items in your queue

#### Status & Control
- `/status` - Check current download status
- `/stop_all` - Stop the current download/extraction
- `/force_stop_all` - Force stop all operations and clean up

## Project Structure

```
subxtract/
├── bot.py                      # Main bot entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── extensions/                 # Discord bot command extensions
│   ├── extractor.py           # Main extraction command
│   ├── queue.py               # Queue display
│   ├── add_to_queue.py        # Add to queue
│   ├── remove_from_queue.py   # Remove from queue
│   ├── clear_queue.py         # Clear queue
│   ├── start_queue.py         # Start processing queue
│   ├── allow_channel.py       # Channel permission management
│   ├── disallow_channel.py    # Remove channel permissions
│   ├── status.py              # Download status
│   ├── stop_all.py            # Stop operations
│   └── force_stop_all.py      # Force stop operations
├── utils/                      # Utility modules
│   ├── aria2_service.py       # Aria2 download management
│   ├── mkv_service.py         # MKV file operations
│   ├── file_utils.py          # File and data management
│   ├── controller.py          # Cancellation event management
│   ├── logger.py              # Logging configuration
│   └── utils.py               # General utilities
├── gen_types/                  # Generated type definitions
│   └── mkvmerge_return_type.py
├── schemas/                    # JSON schemas for validation
│   └── mkvmerge_schema.json
├── data/                       # Runtime data storage
│   ├── allowed_channels.json  # Channel permissions
│   ├── current_download.json  # Active download state
│   └── queue.json             # User download queues
└── temp/                       # Temporary files
    ├── downloads/             # Downloaded files
    └── extracted/             # Extracted content
```

## How It Works

1. **Download Phase**:
   - User submits a URL via `/extract` command
   - Aria2 downloads the content (supports torrents, magnets, direct links)
   - Bot tracks and displays real-time progress
   - Supports cancellation at any point

2. **Extraction Phase**:
   - Scans downloaded files for MKV containers
   - Extracts subtitles, attachments, chapters, and metadata
   - Packages extracted content into zip files
   - Splits large files to meet Discord's upload limit

3. **Upload Phase**:
   - Uploads extracted content to Discord
   - Provides merge commands for split files
   - Displays extraction statistics

4. **Cleanup**:
   - Removes temporary files
   - Clears Aria2 download list
   - Resets state for next operation

## Configuration Details

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | *Required* |
| `ARIA2_RPC_URL` | Aria2 RPC endpoint | `http://localhost:6800/jsonrpc` |
| `ARIA2_RPC_HOST` | Aria2 RPC host | `localhost` |
| `ARIA2_RPC_PORT` | Aria2 RPC port | `6800` |
| `ARIA2_RPC_SECRET` | Aria2 RPC secret token | *(empty)* |
| `TEMP_DIR` | Temporary files directory | `./temp` |
| `DOWNLOAD_DIR` | Download storage directory | `./temp/downloads` |
| `EXTRACT_DIR` | Extraction output directory | `./temp/extracted` |
| `SCHEMAS_DIR` | JSON schemas directory | `./schemas` |
| `ALLOWED_CHANNELS_FILE` | Channel permissions file | `./data/allowed_channels.json` |
| `CURRENT_DL_FILE` | Current download state file | `./data/current_download.json` |
| `QUEUE_FILE` | User queues file | `./data/queue.json` |

## Development

### Adding New Commands

Create a new extension in the `extensions/` directory:

```python
from interactions import Extension, SlashContext, slash_command, check
from utils.utils import is_allowed_channel

class MyCommand(Extension):
    @slash_command()
    @check(is_allowed_channel)
    async def mycommand(self, ctx: SlashContext):
        """Command description"""
        await ctx.send("Hello!")

def setup(bot):
    MyCommand(bot)
```

The bot automatically loads all extensions in the `extensions/` directory.

### Logging

The project uses a custom logger accessible via:

```python
from utils.logger import get_logger

logger = get_logger("module_name")
logger.info("Info message")
logger.error("Error message")
```

## Troubleshooting

### Bot doesn't respond to commands
- Verify the bot is running and connected
- Check that the channel is allowed via `/allow_channel`
- Ensure the bot has proper Discord permissions

### Aria2 connection failed
- Verify Aria2 RPC server is running
- Check `ARIA2_RPC_HOST` and `ARIA2_RPC_PORT` configuration
- Ensure `ARIA2_RPC_SECRET` matches if set

### Extraction fails
- Verify MKVToolNix (`mkvmerge`, `mkvextract`) is installed
- Verify MediaInfo is installed
- Check that all tools are in system PATH

### Large files won't upload
- Files larger than 10MB are automatically split
- Use the provided merge commands to reassemble split files

## License

*Add your license information here*

## Contributing

*Add contribution guidelines here*

## Support

*Add support contact information here*
