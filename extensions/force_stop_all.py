"""ForceStopAll extension for stopping all processes."""

from interactions import Extension, slash_command, SlashContext, Permissions, check
from utils.logger import get_logger
from utils.controller import extraction_cancel_event
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("force_stop_all")

class ForceStopAll(Extension):
    """Extension for stopping all processes."""
    @slash_command(
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    @check(is_allowed_channel)
    async def force_stop_all(self, ctx: SlashContext):
        """Stops all processes (admin only)."""
        await ctx.defer()
        try:
            extraction_cancel_event.set()
            logger.info("Extraction cancellation event fired by %s", ctx.author.id)
            message = await ctx.send("Stopping all processes...")
            if extraction_cancel_event.is_set():
                logger.info("All processes have been forcefully stopped by %s", ctx.author.id)
                await message.edit(content="All processes have been forcefully stopped.")
        except Exception as e:
            await ctx.send(f"An error occurred while stopping all processes: {e}")
            logger.error("Error stopping all processes: %s", e)


def setup(bot):
    """Sets up the ForceStopAll extension."""
    ForceStopAll(bot)
