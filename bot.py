"""Main bot file to run the Discord bot."""

import pkgutil
from typing import Any, cast

import aiohttp
from interactions import Activity, ActivityType, Client, Intents, listen
from interactions.api.gateway.websocket import WebsocketClient
from interactions.models.discord.channel import TYPE_CHANNEL_MAPPING, GuildChannel
from config import DISCORD_TOKEN
from utils.core import get_logger

# Configure logging
logger = get_logger("bot")

# Register newer Discord channel types (e.g., 20 = server-hub) missing in interactions 5.15.0
cast(dict[int, Any], TYPE_CHANNEL_MAPPING).setdefault(20, GuildChannel)

# Convert aiohttp ClientConnectionResetError into ServerDisconnectedError so
# interactions.py reconnects cleanly instead of stopping the shard.
_orig_ws_send = WebsocketClient.send


async def _safe_ws_send(self, *args, **kwargs):
    try:
        return await _orig_ws_send(self, *args, **kwargs)
    except aiohttp.ClientConnectionResetError as exc:
        raise aiohttp.ServerDisconnectedError("Transport closing") from exc


WebsocketClient.send = _safe_ws_send

# Initialize bot with all intents
bot = Client(token=DISCORD_TOKEN, intents=Intents.ALL)

# On start
@listen()
async def on_startup():
    """Handles bot startup events."""
    logger.info("%s has started and is connected to guilds.", bot.user)

    for guild in bot.guilds:
        logger.info("Connected to guild: %s (id: %s)", guild.name, guild.id)
    await bot.change_presence(
        activity=Activity(
            name="SubXtract | /extract",
            type=ActivityType.WATCHING
        )
    )

# Load all extensions in the extensions directory
extension_names = [m.name for m in pkgutil.iter_modules(["extensions"], prefix="extensions.")]

for extension in extension_names:
    bot.load_extension(extension)

bot.start()
