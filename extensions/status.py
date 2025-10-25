"""Status extension for checking current download status."""

from interactions import Extension, slash_command, check, SlashContext
from utils import file_utils
from utils.logger import get_logger
from utils.utils import is_allowed_channel

# Configure logging
logger = get_logger("status")

class Status(Extension):
    """Extension for checking current download status."""
    @slash_command()
    @check(is_allowed_channel)
    async def status(self, ctx: SlashContext):
        """Checks the current status of the current download."""
        await ctx.defer()
        current_dl = file_utils.load_current_dl()
        if not current_dl:
            await ctx.send("No download in progress.")
            logger.info("No download in progress.")
            return

        user_id = current_dl.get("user_id", "")
        guild_id = current_dl.get("guild_id", "")

        # If the command is invoked by the user who started the download
        if str(ctx.author.id) == str(user_id):
            # Check if the download is in the same guild
            if ctx.guild and str(ctx.guild.id) == str(guild_id):
                await ctx.send(f"{ctx.author.mention}, You already have a download in progress.")
            else:
                await ctx.send(
                    f"{ctx.author.mention}, "
                    f"You have a download in progress in another server."
                )
        # If the command is invoked by a different user
        else:
            user = await self.bot.fetch_user(int(user_id)) if user_id else None
            # Check if the download is in the same guild
            if user and ctx.guild:
                if str(ctx.guild.id) == str(guild_id):
                    await ctx.send(f"{user.mention} has a download in progress.")
                elif str(ctx.guild.id) != str(guild_id):
                    await ctx.send(
                        f"{ctx.author.mention}, "
                        f"Another user has a download in progress in another server."
                    )
            else:
                await ctx.send("A download is currently in progress by another user.")

        logger.info("User %s checked the download status.", ctx.author.id)


def setup(bot):
    """Sets up the Status extension."""
    Status(bot)
