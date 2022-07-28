import traceback

import disnake
from disnake.ext import commands
from disnake.ext.commands import Context

from cogs.utils.cog_command_style_parser.sentdebot_command_parser import parse


class CommandConverter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.remove_command("help")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if not message.author.bot:
            if message.content.startswith(self.bot.command_prefix + '.'):
                orig_content = message.content
                try:
                    command_name, args = parse(self.bot.command_prefix, message.content)
                    output = "{}{}".format(
                        self.bot.command_prefix,
                        command_name
                    )
                    if args:
                        output += " " + " ".join(args)
                    message.content = output
                    await self.bot.process_commands(message)
                except Exception:
                    print(traceback.format_exc(chain=True))
                finally:
                    message.content = orig_content

    # on error
    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        if isinstance(error, commands.CommandNotFound):
            return


def setup(bot):
    bot.add_cog(CommandConverter(bot))
