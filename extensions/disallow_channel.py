"""Channel disallow extension for allowing specific channels."""

from interactions import Extension, slash_command, SlashContext, Permissions
from utils import file_utils
from utils.logger import get_logger

# Configure logging
logger = get_logger("disallow_channel")

class DisallowChannel(Extension):
    """Extension for disallowing specific channels."""
    @slash_command(
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def disallow_channel(self, ctx: SlashContext):
        """Disallows current channel to use the bot."""
        await ctx.defer()
        try:
            file_utils.remove_allowed_channel(
                guild_id=str(ctx.guild_id),
                channel_id=str(ctx.channel_id)
            )
            await ctx.send("This channel has been disallowed from using the bot.")
            logger.info("\"%s\" Channel disallowed in \"%s\"", ctx.channel.name, ctx.guild.name if ctx.guild else "DM")
        except Exception as e:
            await ctx.send(f"An error occurred while disallowing this channel: {e}")
            logger.error("Error disallowing channel %s: %s", ctx.channel_id, e)


def setup(bot):
    """Sets up the DisallowChannel extension."""
    DisallowChannel(bot)
