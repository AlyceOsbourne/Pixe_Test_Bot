"""Cog to send a daily dog to the dog channel"""
import datetime
import io
import aiohttp
import requests
import pytz
import disnake
from disnake.ext import commands, tasks

tz = pytz.UTC


class DailyDog(disnake.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if not disnake.utils.get(guild.text_channels, name='dogs'):
                await guild.create_text_channel('dogs')
        await self.daily_dog.start()

    @tasks.loop(hours=12)
    async def daily_dog(self):
        await self.bot.wait_until_ready()

        dogs_channel = disnake.utils.get(self.bot.get_all_channels(), name='dogs')
        if dogs_channel is None:
            return
        messages = await dogs_channel.history(limit=100).flatten()
        for message in messages:
            if message.content.startswith('Here\'s your daily dog!'):
                if message.created_at > tz.localize(datetime.datetime.now() - datetime.timedelta(hours=24)):
                    return

        # if there was no daily dog in the last 24 hours, send one
        async with aiohttp.ClientSession() as session:
            async with session.get(requests.get('https://dog.ceo/api/breeds/image/random').json()['message']) as resp:
                if resp.status != 200:
                    return await dogs_channel.send('Could not download file...')
                data = io.BytesIO(await resp.read())
                # send here is your daily dog
                await dogs_channel.send("Here's your daily dog!", file=disnake.File(data, 'cool_image.png'))


def setup(bot):
    bot.add_cog(DailyDog(bot))
