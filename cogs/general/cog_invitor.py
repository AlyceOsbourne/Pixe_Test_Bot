from disnake.ext import commands, tasks
from disnake.ext.commands import Context
from disnake.ui import Button, View


class Invitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_link = 'https://discordapp.com/oauth2/authorize?client_id={}&permissions=1644971949558&scope=bot'

    class InviteView(View):
        def __init__(self, bot, invite_link):
            self.bot = bot
            super().__init__()
            self.add_item(Button(
                label="Invite!",
                url=invite_link.format(self.bot.user.id),
            )
            )

    @commands.command("invite")
    async def invite(self, ctx: Context):
        await ctx.message.delete(delay=5)
        await ctx.send("Invite me here!", view=self.InviteView(self.bot, invite_link=self.invite_link), delete_after=60)
        await ctx.send(self.invite_link.format(self.bot.user.id))


def setup(bot):
    bot.add_cog(Invitor(bot))
