# cog that gets a list of commands, their args and help string if one is available
from typing import Optional

import disnake
from disnake.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.remove_command("help")

    @commands.command(name='help', help='Get help on a command', aliases=['commands'])
    async def help(self, ctx, *, command_name: Optional[str]):
        await ctx.message.delete()
        embed = disnake.Embed(title="Help")
        if command_name:
            command = self.bot.get_command(command_name)
            if command:  #
                if not command.hidden:
                    embed.description = "{}({}): {}".format(
                        command.name, ", ".join(command.clean_params.keys()), command.help
                    )
                    await ctx.send(embed=embed)
            else:
                await ctx.send(f"Command {command_name} not found")
        else:
            commands = "\n".join(
                "{}({}): {}".format(
                    command.name,
                    ", ".join(command.clean_params.keys()),
                    command.help if command.help else "No help available"
                )
                for command
                in sorted(self.bot.commands, key=lambda c: c.name)
                if not command.hidden
            )
            embed.description = commands
            await ctx.send(embed=embed, delete_after=60)


def setup(bot):
    bot.add_cog(Helper(bot))
