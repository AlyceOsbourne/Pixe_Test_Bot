"""cog that has command to delete n previous messages"""

from disnake.ext import commands


class ChannelSweeper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sweep', aliases=['clean'], hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def sweep(self, ctx, amount):
        if amount == 'all':
            await ctx.channel.purge(limit=None)
        else:
            await ctx.channel.purge(limit=int(amount))
        await ctx.send(f'{amount} messages deleted', delete_after=5)

    @sweep.error
    async def sweep_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the amount of messages to delete!', delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Please specify a valid amount of messages to delete!', delete_after=5)
        else:
            raise error


############
def setup(bot):
    bot.add_cog(ChannelSweeper(bot))
