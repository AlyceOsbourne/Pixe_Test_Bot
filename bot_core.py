# use nextcord.ext.commands.PixieBot to create the bot
import os

import nextcord
from nextcord.ext import commands, tasks
from nextcord.ui import button
from dotenv import load_dotenv
from os import getenv
from os.path import join, dirname, isdir, isfile, exists
import asyncio

from nextcord.ext.commands import Context

load_dotenv(join(dirname(__file__), '.env'))

if getenv('TOKEN') is None or getenv('PREFIX') is None:
    if not isfile(join(dirname(__file__), '.env')):
        with open(join(dirname(__file__), '.env'), 'w') as f:
            f.write('TOKEN=\nPREFIX=\n')
    raise Exception('TOKEN and PREFIX must be set in the .env file')


class PixieBot(commands.Bot):
    cog_directories = (
        'admin',
        'general',
        'utils',
        'games',
        'music',
        'moderation',
        'metrics'
    )

    def __init__(self):
        super().__init__(
            command_prefix=getenv('PREFIX'),
            intents=nextcord.Intents.all()
        )

    def load_cogs(self):
        cogs_path = join(dirname(__file__), 'cogs')
        if not exists(cogs_path):
            os.mkdir(cogs_path)
        for cog_directory in self.cog_directories:
            dir_path = join(cogs_path, cog_directory)
            if not exists(dir_path):
                os.mkdir(dir_path)
            else:
                for file in os.listdir(dir_path):
                    if file.startswith('cog_'):
                        if file.endswith('.py'):
                            self.load_extension(f'cogs.{cog_directory}.{file[:-3]}')
                        elif isdir(join(dir_path, file)):
                            if isfile(join(dir_path, file, '__init__.py')):
                                self.load_extension(f'cogs.{cog_directory}.{file}')

    # on ready event
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.user.name} is online!')
        print(f'{self.user.id}')
        print(f'https://discordapp.com/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=8')
        await self.user.edit(username=self.__class__.__name__)

    # command to invite bot, only the author can see this

    def run(self):
        self.load_cogs()
        super().run(getenv('TOKEN'), reconnect=True)


if __name__ == "__main__":
    bot = PixieBot()

    bot.run()
