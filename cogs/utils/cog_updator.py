'''cog that scans all loaded cogs, gets their file, and updates them if they are outdated'''
import os
import asyncio
import inspect
from nextcord.ext import commands, tasks


class CogUpdator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cogs = {}

    # on ready
    @commands.Cog.listener()
    async def on_ready(self):
        for cog in self.bot.cogs:
            cog = self.bot.cogs[cog]
            cog_file = inspect.getfile(cog.__class__)
            last_updated = os.path.getmtime(cog_file)
            self.cogs[cog.__class__.__name__] = last_updated
        self.check_cogs.start()

    @tasks.loop(seconds=60, reconnect=True)
    async def check_cogs(self):

        for cog in list(self.cogs):
            cog = self.bot.cogs[cog]
            cog_file = inspect.getfile(cog.__class__)
            if cog_file == __file__:
                continue
            last_updated = os.path.getmtime(cog_file)
            if last_updated > self.cogs[cog.__class__.__name__]:
                cog_file = "cogs" + cog_file.split('cogs')[1].replace('\\', '.')[:-3]
                try:
                    self.bot.reload_extension(cog_file)
                except Exception as e:
                    print(f'Failed to reload cog {cog_file}')
                    print(e)
                else:
                    print(f'Reloaded cog {cog_file}')
                    self.cogs[cog.__class__.__name__] = last_updated

    # before loop
    @check_cogs.before_loop
    async def before_check_cogs(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(CogUpdator(bot))
