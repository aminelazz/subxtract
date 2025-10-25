"""StopAll extension for stopping all processes."""

from interactions import Extension, SlashContext, slash_command, check
from utils import file_utils
from utils.logger import get_logger
from utils.controller import extraction_cancel_event
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("stop_all")

class StopAll(Extension):
    """Extension for stopping all processes (if initiated by the same user)."""
    @slash_command()
    @check(is_allowed_channel)
    async def stop_all(self, ctx: SlashContext):
        """Stops all processes (if initiated by the same user)."""
        await ctx.defer()
        try:
            current_dl = file_utils.load_current_dl()
            if not current_dl:
                await ctx.send("No active processes to stop.")
                logger.info("No active processes to stop.")
                return

            if ctx.author.id != int(current_dl.get("user_id", 0)):
                await ctx.send("You do not have permission to stop the current processes.")
                logger.warning(
                    "User %s attempted to stop processes without permission.",
                    ctx.author.id
                )
                return

            extraction_cancel_event.set()
            logger.info("Extraction cancellation event fired by %s", ctx.author.id)
            message = await ctx.send("Stopping all processes...")
            if extraction_cancel_event.is_set():
                logger.info("All processes have been stopped by %s", ctx.author.id)
                await message.edit(content="All processes have been stopped.")
        except Exception as e:
            await ctx.send(f"An error occurred while stopping all processes: {e}")
            logger.error("Error stopping all processes: %s", e)


def setup(bot):
    """Sets up the StopAll extension."""
    StopAll(bot)
