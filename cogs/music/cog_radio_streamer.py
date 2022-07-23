# cog to stream music from a radio station url to the radio voice channel


import asyncio
import sys

import nextcord
from nextcord import Interaction, VoiceClient, FFmpegPCMAudio

from nextcord.ext import commands, tasks
from nextcord.ext.commands import Context
import pyradios

sys.path.append("libs")

# get ffmpeg executable path
ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn',
    'executable': 'libs/ffmpeg',
}


class RadioStreamer(commands.Cog):
    class RadioSelect(nextcord.ui.Select):
        def __init__(self, stations, timeout):
            super().__init__(
                placeholder="Select a radio station",
                min_values=1,
                max_values=1,
                options=[
                    nextcord.SelectOption(label=k, value=v)
                    for (k, v) in stations.items()
                ],
            )
            self.timeout = timeout

        # await result
        async def result(self):
            current = 0
            sleep_time = 0.2
            while len(self.values) == 0 and current < self.timeout:
                await asyncio.sleep(sleep_time)
                current += sleep_time
            if len(self.values) == 0:
                raise asyncio.TimeoutError
            return self.values[0]

    class RadioSelectView(nextcord.ui.View):
        def __init__(self, stations, timeout=30):
            super().__init__(timeout=timeout)
            self.add_item(RadioStreamer.RadioSelect(stations, timeout))

        def result(self):
            return self.children[0].result()

    def __init__(self, bot):
        self.bot = bot
        self.clients: dict[int: tuple[VoiceClient, FFmpegPCMAudio]] = dict()

    # on ready
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.name == "radio":
                    if isinstance(channel, nextcord.VoiceChannel):
                        break
            else:
                await guild.create_voice_channel("radio")
        self.loop_radio_perms.start()

    @commands.command(name="radio", aliases=["stream"])
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def radio(self, ctx: Context, *, url):
        try:
            await ctx.message.delete()
        except nextcord.HTTPException:
            pass
        radio_channel = None
        if ctx.author.voice:
            radio_channel = ctx.author.voice.channel
        else:
            for channel in ctx.guild.channels:
                if channel.name == "radio":
                    if isinstance(channel, nextcord.VoiceChannel):
                        radio_channel = channel
                        break

        if radio_channel is None:
            return

        if radio_channel.id in self.clients and self.clients[radio_channel.id][0].is_connected:
            vc, stream = self.clients[radio_channel.id]
            if vc.is_playing():
                vc.stop()
                stream.cleanup()
                del self.clients[radio_channel.id]
                await asyncio.sleep(1)

        elif radio_channel.id in self.clients and not self.clients[radio_channel.id][0].is_connected:
            vc, stream = self.clients[radio_channel.id]
            vc.connect(radio_channel)
        else:
            vc = await radio_channel.connect()

        # move user to radio channel
        if ctx.author.voice:
            await ctx.author.move_to(radio_channel)

        if not ctx.author.voice:
            try:
                await ctx.send(
                    f"Please join the radio channel {radio_channel.mention}",
                    delete_after=30,
                )
                timeout = 30
                current = 0
                sleep_time = 0.2
                while len(radio_channel.members) < 2 and current < timeout:
                    await asyncio.sleep(sleep_time)
                    current += sleep_time
                if radio_channel.id not in self.clients:
                    raise asyncio.TimeoutError
            except asyncio.TimeoutError:
                await ctx.send(
                    "Timed out waiting for user to join radio channel",
                    delete_after=30,
                )
                return

        stream = FFmpegPCMAudio(url, **ffmpegopts)
        self.clients[radio_channel.id] = (vc, stream)

        vc.play(stream)
        current_playing_embed = nextcord.Embed(
            title="Now Playing",
            color=0x00ff00,
        )
        current_playing_embed.add_field(
            name="Station",
            value=url,
            inline=False,
        )

        current_playing_embed.set_footer(text=ctx.author.name, icon_url=ctx.author.display_avatar.url)

        current = await ctx.send(embed=current_playing_embed)
        while vc.is_playing():
            await asyncio.sleep(1)
            if len(radio_channel.members) == 1:
                break
        vc.stop()
        stream.cleanup()
        self.clients.pop(radio_channel.id)
        current_playing_embed.clear_fields()
        current_playing_embed.colour = 0xFF0000
        current_playing_embed.add_field(
            name="Station",
            value="Stopped",
            inline=False,
        )
        current_playing_embed.add_field(
            name="Thanks for listening!",
            value=":heart:",
            inline=False,
        )
        await current.edit(embed=current_playing_embed)
        await current.delete(delay=5)

    @commands.command(name="radio_search", aliases=["radio_search_list", 'search_radio'])
    async def radio_search(self, ctx: Context, *, query: str):
        client = pyradios.RadioBrowser()
        found = client.search(name=query, order='votes', limit=25)

        if len(found) == 0:
            found = client.search(tag=query, order='votes', limit=25)

        if len(found) == 0:
            await ctx.send("No stations found", delete_after=5)
            await ctx.message.delete()
            return
        stations = {}
        for station in found:
            station_name, station_url = station['name'], station['url']
            if any([
                len(station_name) > 100,
                len(station_url) > 100,
                station_name in stations,
                station_url in stations.values()
            ]):
                continue
            stations[station_name] = station_url
            if len(stations) == 25:
                break

        select_view = RadioStreamer.RadioSelectView(stations)
        msg = await ctx.send("Select a radio station", view=select_view)
        try:
            result = await select_view.result()
        except asyncio.TimeoutError:
            select_view.stop()
            await msg.delete()
            return
        select_view.stop()
        await msg.delete()
        await self.radio(ctx, url=result)

    # stop radio
    @commands.command(name="radio_stop")
    async def radio_stop(self, ctx: Context):
        if ctx.author.voice:
            vc, stream = self.clients[ctx.author.voice.channel.id]
            if vc.is_playing():
                vc.stop()
                stream.cleanup()
            else:
                await ctx.send("Radio not playing")
        else:
            await ctx.send("Not in a voice channel")
        await ctx.message.delete()

    @radio.error
    async def radio_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Bad argument", delete_after=5)
        else:
            await ctx.send(error, delete_after=30)
        raise error

    @radio_search.error
    async def radio_search_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Bad argument", delete_after=5)
        else:
            await ctx.send(error, delete_after=30)
        raise error

    # loop to get each guild's radio channel and set the perms so only the bot can speak, everyone else is muted
    @tasks.loop(seconds=5)
    async def loop_radio_perms(self):
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if channel.id in self.clients:
                    vc, stream = self.clients[channel.id]
                    if vc.is_playing():
                        for member in channel.members:
                            if member.id == self.bot.user.id:
                                continue
                            await member.edit(mute=True)
                    else:
                        for member in channel.members:
                            if member.id == self.bot.user.id:
                                continue
                            await member.edit(mute=False)


def setup(bot):
    bot.add_cog(RadioStreamer(bot))
