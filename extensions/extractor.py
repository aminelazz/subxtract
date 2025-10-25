"""Downloader extension for managing downloads via Aria2."""

from interactions import Extension, SlashContext, OptionType
from interactions import slash_command, slash_option, check
from utils import aria2_service, utils, file_utils
from utils.logger import get_logger

# Configure logging
logger = get_logger("extractor")

class Extractor(Extension):
    """Extension for downloading, managing MKV extraction and upload."""
    @slash_command()
    @check(utils.is_allowed_channel)
    @slash_option(
        name="url",
        description="The URL of the torrent or magnet link or direct download link to download.",
        required=True,
        opt_type=OptionType.STRING,
    )
    async def extract(self, ctx: SlashContext, url: str):
        """Downloads using Aria2, Extracts MKV info, subs, attachments, and chapters, then uploads the results."""
        await ctx.defer()

        # Start download and extraction process
        completed = await utils.download_and_extract(ctx, url)

        # Check if completed successfully
        if completed is True:
            logger.info("Extraction process completed for all files.")
            await ctx.send(f"{ctx.author.mention}, Extraction process completed for all files, Have Fun :grin:")

        #region ---- Clean up ----
        try:
            aria2_service.remove_all_downloads(force=True)
        except Exception as e:
            logger.error("Error removing downloads during cleanup: %s", e)
        file_utils.clear_current_dl()
        # file_utils.clear_temp()
        #endregion

def setup(bot):
    """Sets up the Extractor extension."""
    Extractor(bot)
