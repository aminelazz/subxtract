"""Logs extension for sending log files."""

from pathlib import Path
from interactions import Extension, SlashContext, slash_command, check, slash_option, OptionType, File

from utils.core import is_allowed_channel
from utils.logger import get_logger
from utils.file_utils import read_log_file

# Configure logging
logger = get_logger(__name__)

# Define log file paths
BOT_LOG=Path("/tmp/bot.log")
ARIA2_LOG=Path("/tmp/aria2.log")
CF_LOG=Path("/tmp/cf_tunnel.log")
WEB_LOG=Path("/tmp/web_server.log")

class Logs(Extension):
    """Extension for sending log files."""
    @slash_command()
    @check(is_allowed_channel)
    @slash_option(
        name="log_type",
        description="Choose what log data to send.",
        required=True,
        opt_type=OptionType.STRING,
        choices=[
            {"name": "Bot", "value": "bot"},
            {"name": "Aria2", "value": "aria2"},
            {"name": "Cloudflare Tunnel", "value": "cf_tunnel"},
            {"name": "Web Server", "value": "web_server"},
        ],
    )
    async def logs(self, ctx: SlashContext, log_type: str):
        """Sends the requested log file to the user."""

        # Validate log_type
        log_type = log_type.lower()
        if log_type not in ["bot", "aria2", "cf_tunnel", "web_server"]:
            await ctx.send("Invalid log type. Please choose from bot, aria2, cf_tunnel, or web_server.")
            return

        # Read the appropriate log file based on the log_type
        log_file = None
        log_name = None
        if log_type == "bot":
            logger.info("Sending bot log file.")
            log_file = read_log_file(BOT_LOG)
            log_name = "bot.log"
        elif log_type == "aria2":
            logger.info("Sending Aria2 log file.")
            log_file = read_log_file(ARIA2_LOG)
            log_name = "aria2.log"
        elif log_type == "cf_tunnel":
            logger.info("Sending Cloudflare Tunnel log file.")
            log_file = read_log_file(CF_LOG)
            log_name = "cf_tunnel.log"
        elif log_type == "web_server":
            logger.info("Sending Web Server log file.")
            log_file = read_log_file(WEB_LOG)
            log_name = "web_server.log"

        # Check if the log file was successfully read and send it to the user
        if log_file and log_name:
            await ctx.send(
                file=File(
                    file=log_file,
                    file_name=log_name,
                )
            )
        else:
            logger.error("Failed to read log file: %s", log_name)
            await ctx.send("Log file not found.")

def setup(bot):
    """Sets up the Logs extension."""
    Logs(bot)
