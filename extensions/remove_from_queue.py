"""RemoveFromQueue extension for removing links from the queue."""

from interactions import Extension, SlashContext, slash_command, check, slash_option, OptionType
from utils import file_utils
from utils.logger import get_logger
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("remove_from_queue")

class RemoveFromQueue(Extension):
    """Extension for removing links from the queue."""
    @slash_command()
    @check(is_allowed_channel)
    @slash_option(
        name="links",
        description="The links to remove from the download queue, separated by commas.",
        required=True,
        opt_type=OptionType.STRING,
    )
    async def remove_from_queue(self, ctx: SlashContext, links: str):
        """Removes links from the download queue, separated by commas (,)."""
        await ctx.defer()
        # try:
        links_list = [link.strip() for link in links.split(",") if link.strip()]
        if not links_list:
            await ctx.send("No valid links provided.")
            return
        
        difference = file_utils.remove_from_queue(str(ctx.author.id), links_list)
        await ctx.send(f"Removed {difference} links from your download queue.")
        logger.info("User %s removed %d links from the queue.", str(ctx.author.id), difference)
        # except Exception as e:
        #     await ctx.send(f"An error occurred while adding links to the queue: {e}")
        #     logger.error("Error adding links to the queue: %s", e)


def setup(bot):
    """Sets up the StopAll extension."""
    RemoveFromQueue(bot)
