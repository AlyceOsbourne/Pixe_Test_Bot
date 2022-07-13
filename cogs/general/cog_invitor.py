from nextcord.ext import commands, tasks
from nextcord.ext.commands import Context
from nextcord.ui import Button, View


class Invitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class InviteView(View):
        def __init__(self, bot):
            self.bot = bot
            super().__init__()
            self.add_item(Button(
                label="Invite!",
                url=f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8')
            )

    @commands.command("invite")
    async def invite(self, ctx: Context):
        await ctx.message.delete(delay=5)
        await ctx.send("Invite me here!", view=self.InviteView(self.bot), delete_after=10)

def setup(bot):
    bot.add_cog(Invitor(bot))
