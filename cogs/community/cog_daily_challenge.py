"""
Cog to provide a daily challenge to the challenge channel
Parses from projecteuler.net/recent
"""
import datetime

import disnake
import pytz
from disnake.ext import commands, tasks

import requests
from bs4 import BeautifulSoup

tz = pytz.UTC


class DailyChallenge(commands.Cog):
    # a cog to download the challenge from project euler
    def __init__(self, bot):
        self.bot = bot

    # on ready, check to see if all guilds have a challenge channel
    # if not, create one
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if not disnake.utils.get(guild.text_channels, name='challenge'):
                await guild.create_text_channel('challenge')
        await self.daily_challenge.start()

    @tasks.loop(hours=12)
    async def daily_challenge(self):
        await self.bot.wait_until_ready()
        channels = disnake.utils.get(self.bot.get_all_channels(), name='challenge')
        if channels is not None:
            soup = BeautifulSoup(requests.get('https://projecteuler.net/recent').text, 'html.parser')
            href = soup.find('table', {'id': 'problems_table'}).find_all('tr')[1].find('a')['href']
            challenge = f'https://projecteuler.net/{href}'
            # get history since yesterday
            async for message in channels.history(after=datetime.datetime.now(tz) - datetime.timedelta(days=1)):
                if message.author == self.bot.user:
                    if message.content.startswith('Here is your challenge!'):
                        if message.embeds:
                            if challenge in message.embeds[0].description:
                                return
            await channels.send("Here is your challenge!", embed=disnake.Embed(description=challenge))


def setup(bot):
    bot.add_cog(DailyChallenge(bot))
