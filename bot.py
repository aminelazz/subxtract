"""Main bot file to run the Discord bot."""

import pkgutil

from interactions import Activity, ActivityType, Client, Intents, listen
from config import DISCORD_TOKEN
from utils.utils import get_logger

# Configure logging
logger = get_logger("bot")

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
