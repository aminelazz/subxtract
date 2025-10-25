"""AllowChannel extension for allowing specific channels."""

from interactions import Extension, slash_command, SlashContext, Permissions
from utils import file_utils
from utils.logger import get_logger

# Configure logging
logger = get_logger("allow_channel")

class AllowChannel(Extension):
    """Extension for allowing specific channels."""
    @slash_command(
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def allow_channel(self, ctx: SlashContext):
        """Allows current channel to use the bot."""
        await ctx.defer()
        try:
            file_utils.save_allowed_channels(
                guild_id=str(ctx.guild_id),
                channel_id=str(ctx.channel_id)
            )
            await ctx.send("This channel has been allowed to use the bot.")
            logger.info(
                '"%s" Channel allowed in "%s"',
                ctx.channel.name,
                ctx.guild.name if ctx.guild else "DM"
            )
        except Exception as e:
            await ctx.send(f"An error occurred while allowing this channel: {e}")
            logger.error("Error allowing channel %s: %s", ctx.channel_id, e)


def setup(bot):
    """Sets up the AllowChannel extension."""
    AllowChannel(bot)
