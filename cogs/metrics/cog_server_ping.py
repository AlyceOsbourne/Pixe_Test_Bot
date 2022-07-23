# cog with command to check the bot latency, connection speed etc etc etc
import nextcord
from nextcord.ext import commands
import speedtest
from nextcord.ext.commands import Context


class ConnectionStatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("check_connection_status", aliases=["st"])
    async def connection_stats(self, ctx: Context):
        await ctx.message.delete()
        embed = nextcord.Embed(description="Speed Test")

        confirm = await ctx.send(embed=embed)

        st = speedtest.Speedtest()
        await confirm.edit(embed=embed)

        dl = st.download() / 1024 / 1024
        embed.add_field(name="Download Speed:", value=F"`{dl:.2f} Mbps`")
        await confirm.edit(embed=embed)

        ul = st.upload() / 1024 / 1024
        embed.add_field(name="Upload Speed:", value=F"`{ul:.2f} Mbps`")
        await confirm.edit(embed=embed)

        st.get_best_server()
        ping = st.results.ping
        embed.add_field(name="Ping:", value=f"`{ping:.0f}`")
        await confirm.edit(embed=embed)

        r = int(min(255, max(0, dl * 20)))
        g = int(min(255, max(0, ul * 20)))
        b = int(min(255, max(0, 255 - (ping * 2))))
        embed.colour = nextcord.Colour.from_rgb(r, g, b)
        embed.set_footer(text="'¯\_(ツ)_/¯'", icon_url=ctx.bot.user.display_avatar.url)
        await confirm.edit(embed=embed, delete_after=60)


def setup(bot):
    bot.add_cog(ConnectionStatusCog(bot))
