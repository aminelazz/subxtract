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
    
        embed.set_thumbnail(url=bot_infos["bot"]["avatar"])
        # embed.set_author(name='Available commands', icon_url=bot.user.avatar.url)
        for cmd in cmds:
            params: list[dict] = cmd.get("options", [])
            params_str = " ".join([f"[{p.get('name', '')}]" for p in params])
            embed.add_field(name=f'/{cmd["name"]} {params_str}', value=cmd["description"], inline=False)
        # embed.set_footer(text="This is the footer of the embed.")
    
        await ctx.send(content=None, embeds=[embed])


def setup(bot):
    """Sets up the Status extension."""
    Help(bot)
