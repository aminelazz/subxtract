"""StartQueue extension for starting the download queue."""

from interactions import Extension, SlashContext, OptionType
from interactions import slash_command, slash_option, check
from utils import aria2_service, utils, file_utils
from utils.logger import get_logger
from utils.controller import extraction_cancel_event

# Configure logging
logger = get_logger("start_queue")

class StartQueue(Extension):
    """
    Extension for downloading, managing MKV extraction and upload for multiple links in a queue.
    """
    @slash_command()
    @check(utils.is_allowed_channel)
    @slash_option(
        name="type",
        description="Choose what to extract from all MKV files in the queue. Defaults to queue item's configured type.",
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
    async def start_queue(self, ctx: SlashContext, type: str = None):
        """Downloads, Extracts, then uploads the results from multiple links in the queue."""
        await ctx.defer()

        # Get the queue
        queue = file_utils.get_user_queue(str(ctx.author.id))

        if not queue or not queue.links:
            await ctx.send(
                f"{ctx.author.mention}, "
                f"Your queue is empty. Please add links to the queue before starting the download."
            )
            return

        queue_items = queue.links.copy()
        links_size = len(queue_items)

        logger.info(
            "Starting queue processing for user %s with %d links.",
            str(ctx.author.id), links_size
        )
        await ctx.send(f"Starting the download and extraction process for {links_size} links.")

        i = 1
        # Start download and extraction process
        for queue_item in queue_items:
            # Extract link and type from queue item
            url = queue_item.get("link", queue_item) if isinstance(queue_item, dict) else queue_item
            extraction_type = type if type else queue_item.get("type", "all_without_audio") if isinstance(queue_item, dict) else "all_without_audio"

            # Check for cancellation
            if extraction_cancel_event.is_set():
                aria2_service.remove_all_downloads(force=True)
                file_utils.clear_current_dl()
                file_utils.clear_temp()
                await ctx.send(content="queue processing has been cancelled.")
                break

            logger.info("Starting download and extraction for URL: %s with type: %s", url, extraction_type)
            completed = await utils.download_and_extract(ctx, url, extraction_type=extraction_type)

            # Check if completed successfully
            if completed is True:
                # Remove the specific URL from queue
                queue_items_remaining = [item for item in queue_items if (item.get("link") if isinstance(item, dict) else item) != url]
                file_utils.clear_user_queue(str(ctx.author.id))
                file_utils.save_queue(str(ctx.author.id), queue_items_remaining)
                logger.info("Extraction process completed for (%d/%d) links.", i, links_size)
                await ctx.send(
                    f"{ctx.author.mention}, "
                    f"Extraction process completed for ({i}/{links_size}) links.\n"
                    f"{'Processing next link...' if i < links_size else ''}"
                )
            else:
                logger.error("Extraction process failed for URL: %s", url)
                await ctx.send(
                    f"{ctx.author.mention}, "
                    f"Extraction process failed for the link:\n"
                    f"{url}\n\n"
                    f"{'Skipping to the next link...' if i < links_size else ''}"
                )

            # Clean up after each link
            try:
                aria2_service.remove_all_downloads(force=True)
            except Exception as e:
                logger.error("Error removing downloads during cleanup: %s", e)
            file_utils.clear_current_dl()
            try:
                file_utils.clear_temp()
            except Exception as e:
                logger.error("Error clearing temp files: %s", e)
            # Increment link counter
            i += 1


        logger.info("Extraction process completed for all links.")
        await ctx.send(
            f"{ctx.author.mention}, Extraction process completed for all links, Have Fun :grin:"
        )

        #region ---- Clean up ----
        try:
            aria2_service.remove_all_downloads(force=True)
        except Exception as e:
            logger.error("Error removing downloads during cleanup: %s", e)
        file_utils.clear_current_dl()
        try:
            file_utils.clear_temp()
        except Exception as e:
            logger.error("Error clearing temp files: %s", e)
        #endregion

def setup(bot):
    """Sets up the Extractor extension."""
    StartQueue(bot)
