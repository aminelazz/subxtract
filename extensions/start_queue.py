"""StartQueue extension for starting the download queue."""

from interactions import Extension, SlashContext
from interactions import slash_command, check
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
    async def start_queue(self, ctx: SlashContext):
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

        links = queue.links.copy()
        links_size = len(links)

        logger.info(
            "Starting queue processing for user %s with %d links.",
            str(ctx.author.id), links_size
        )
        await ctx.send(f"Starting the download and extraction process for {links_size} links.")

        i = 1
        # Start download and extraction process
        for url in links:
            # Check for cancellation
            if extraction_cancel_event.is_set():
                aria2_service.remove_all_downloads(force=True)
                file_utils.clear_current_dl()
                file_utils.clear_temp()
                await ctx.send(content="queue processing has been cancelled.")
                break

            logger.info("Starting download and extraction for URL: %s", url)
            completed = await utils.download_and_extract(ctx, url)

            # Check if completed successfully
            if completed is True:
                queue.links.remove(url)
                file_utils.clear_user_queue(str(ctx.author.id))
                file_utils.save_queue(str(ctx.author.id), queue.links)
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
