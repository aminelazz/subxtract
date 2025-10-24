"""ClearQueue extension for clearing user queues."""

from interactions import Extension, SlashContext, slash_command, check, slash_option, OptionType
from utils import file_utils
from utils.logger import get_logger
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("clear_queue")

class ClearQueue(Extension):
    """Extension for clearing user queues."""
    @slash_command()
    @check(is_allowed_channel)
    async def clear_queue(self, ctx: SlashContext):
        """Clears the user's download queue."""
        await ctx.defer()
        file_utils.clear_user_queue(str(ctx.author.id))
        await ctx.send("Your download queue has been cleared.")
        logger.info("User %s cleared their download queue.", str(ctx.author.id))


def setup(bot):
    """Sets up the ClearQueue extension."""
    ClearQueue(bot)