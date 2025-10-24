"""Queue extension for managing user download queues."""

from interactions import Extension, SlashContext, slash_command, check
from utils import file_utils
from utils.logger import get_logger
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("queue")

class Queue(Extension):
    """Extension for showing user's queue."""
    @slash_command()
    @check(is_allowed_channel)
    async def queue(self, ctx: SlashContext):
        """Shows the user's download queue."""
        await ctx.defer()
        queue = file_utils.load_queue()
        if not queue:
            await ctx.send("Your download queue is empty.")
            return

        user_queue = next((item for item in queue if item.user_id == str(ctx.author.id)), None)
        if user_queue is None or not user_queue.links:
            await ctx.send("Your download queue is empty.")
            return

        user_queue_str = "\n- ".join(user_queue.links)
        await ctx.send(
            f"Your download queue:\n"
            f"```- {user_queue_str}```"
        )


def setup(bot):
    """Sets up the Queue extension."""
    Queue(bot)
