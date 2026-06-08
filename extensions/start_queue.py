"""AddToQueue extension for adding links to the download queue."""

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
    @slash_option(
        name="type",
        description="Extraction type for these links (defaults to all_without_audio).",
        required=False,
        opt_type=OptionType.STRING,
        choices=[
            {"name": "Subtitles", "value": "subtitles"},
            {"name": "Attachments", "value": "attachments"},
            {"name": "Chapters", "value": "chapters"},
            {"name": "Audio", "value": "audio"},
            {"name": "All", "value": "all"},
            {"name": "All (Without Audio)", "value": "all_without_audio"},
        ],
    )
    async def add_to_queue(self, ctx: SlashContext, links: str, type: str = "all_without_audio"):
        """Adds links to the download queue, separated by commas (,)."""
        await ctx.defer()
        # try:
        links_list = [link.strip() for link in links.split(",") if link.strip()]
        if not links_list:
            await ctx.send("No valid links provided.")
            return

        added = file_utils.save_queue(str(ctx.author.id), links_list, extraction_type=type)
        await ctx.send(f"Added {added} links to your download queue with extraction type: **{type}**.")
        logger.info("User %s added %d links to the queue with type %s.", str(ctx.author.id), added, type)
        # except Exception as e:
        #     await ctx.send(f"An error occurred while adding links to the queue: {e}")
        #     logger.error("Error adding links to the queue: %s", e)


def setup(bot):
    """Sets up the StopAll extension."""
    AddToQueue(bot)
