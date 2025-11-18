"""Help extension for showing various bot commands."""

from interactions import Embed, Extension, slash_command, check, SlashContext
from utils.logger import get_logger
from utils.utils import get_bot_infos, get_commands, is_allowed_channel

# Configure logging
logger = get_logger("help")

class Help(Extension):
    """Extension for showing help information."""
    @slash_command()
    @check(is_allowed_channel)
    async def help(self, ctx: SlashContext):
        """Shows the help information for the bot commands."""
        await ctx.defer()

        embed = Embed(
            title="SubXtract Help",
            description="All SubXtract Commands",
            color="#800080"  # You can set the color of the embed
        )

        bot_infos = get_bot_infos()
        cmds: list[dict] = get_commands()

        # Build a valid thumbnail URL. Discord application API may return an
        # avatar hash rather than a full URL, which causes the embed error
        # "Not a well formed URL". Construct a CDN URL when necessary and
        # only set the thumbnail if we have a valid URL.
        bot_avatar = bot_infos.get("bot", {}).get("avatar")
        bot_id = bot_infos.get("bot", {}).get("id") or bot_infos.get("id")

        thumbnail_url = None
        if bot_avatar:
            # If the API already returned a full URL, use it directly.
            if isinstance(bot_avatar, str) and bot_avatar.startswith("http"):
                thumbnail_url = bot_avatar
            else:
                # Try to construct a CDN URL from id + avatar hash.
                if bot_id:
                    ext = "gif" if str(bot_avatar).startswith("a_") else "png"
                    thumbnail_url = f"https://cdn.discordapp.com/avatars/{bot_id}/{bot_avatar}.{ext}?size=1024"

        # Only set thumbnail if it's a well-formed http(s) URL
        if thumbnail_url and (thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://")):
            embed.set_thumbnail(url=thumbnail_url)
        # embed.set_author(name='Available commands', icon_url=bot.user.avatar.url)
        for cmd in cmds:
            params: list[dict] = cmd.get("options", [])
            params_str = " ".join([f"[{p.get('name', '')}]" for p in params])
            embed.add_field(
                name=f'/{cmd["name"]} {params_str}',
                value=cmd["description"],
                inline=False
            )
        # embed.set_footer(text="This is the footer of the embed.")

        await ctx.send(content=None, embeds=[embed])


def setup(bot):
    """Sets up the Status extension."""
    Help(bot)
