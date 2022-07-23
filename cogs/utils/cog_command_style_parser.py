import traceback

import nextcord
from nextcord.ext import commands


class CommandConverter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.remove_command("help")

    @commands.command(name='test', help='Test command')
    async def test(self, ctx, *, code: str):
        await ctx.send(f"```{code}```")

    def parse_args(self, args_string):
        args = []
        arg = ""
        in_parentheses = None
        for ch in args_string:
            if ch in ("\"", "\'"):
                if in_parentheses is None:
                    if arg != "":
                        raise SyntaxError

                    in_parentheses = ch
                    continue
                elif ch == in_parentheses:
                    in_parentheses = None
                    continue
            elif ch == "," and in_parentheses is None:
                args.append(arg)
                arg = ""
                continue
            arg += ch
        if arg != "":
            args.append(arg)
        return args

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not message.author.bot:
            if message.content.startswith(self.bot.command_prefix + '.'):
                orig_content = message.content
                try:
                    content = message.content[len(self.bot.command_prefix + '.'):]
                    index = content.find("(")
                    command_name, args = content[:index], self.parse_args(content[index + 1:-1])
                    output = "{}{}".format(
                        self.bot.command_prefix,
                        command_name
                    )
                    if args:
                        print(args)
                        output += " " + " ".join(args)
                    message.content = output
                    await self.bot.process_commands(message)
                except Exception:
                    print(traceback.format_exc())
                finally:
                    message.content = orig_content

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.send(traceback.format_exc())
            print(traceback.format_exc())


def setup(bot):
    bot.add_cog(CommandConverter(bot))
