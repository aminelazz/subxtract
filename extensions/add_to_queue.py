"""StopAll extension for stopping all processes."""

from interactions import Extension, SlashContext, slash_command, check, slash_option, OptionType
from utils import file_utils
from utils.logger import get_logger
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("add_to_queue")

class AddToQueue(Extension):
    """Extension for adding links to the queue."""
    @slash_command()
    @check(is_allowed_channel)
    @slash_option(
        name="links",
        description="The links to add to the download queue, separated by commas.",
        required=True,
        opt_type=OptionType.STRING,
    )
    async def add_to_queue(self, ctx: SlashContext, links: str):
        """Adds links to the download queue, separated by commas (,)."""
        await ctx.defer()
        # try:
        links_list = [link.strip() for link in links.split(",") if link.strip()]
        if not links_list:
            await ctx.send("No valid links provided.")
            return
        
        added = file_utils.save_queue(str(ctx.author.id), links_list)
        await ctx.send(f"Added {added} links to your download queue.")
        logger.info("User %s added %d links to the queue.", str(ctx.author.id), added)
        # except Exception as e:
        #     await ctx.send(f"An error occurred while adding links to the queue: {e}")
        #     logger.error("Error adding links to the queue: %s", e)


def setup(bot):
    """Sets up the StopAll extension."""
    AddToQueue(bot)
