# cog to stream music from a radio station url to the radio voice channel
import asyncio
import sys

import disnake
from disnake import Interaction, VoiceClient, FFmpegPCMAudio, Guild

from disnake.ext import commands, tasks
from disnake.ext.commands import Context
import pyradios

sys.path.append("libs")

# get ffmpeg executable path
ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn',
    'executable': 'libs/ffmpeg',
}
pyradio = pyradios.RadioBrowser()


def search_radio_channels(tag, query):
    radio_list = pyradio.search(**{tag: query}, limit=25)
    if len(radio_list) != 0:
        return radio_list


def create_select_option_list(stations):
    return [disnake.SelectOption(label=station, value=station) for station in stations if len(station) < 100]


def get_radio_stream(radio_url):
    return FFmpegPCMAudio(
        radio_url,
        **ffmpegopts
    )


def now_playing_embed(radio_data):
    embed = disnake.Embed(title="Now Playing")
    embed.add_field(name="Station Name:", value=radio_data["name"], inline=False)
    embed.add_field(name="Url", value=radio_data["url_resolved"], inline=False)
    embed.add_field(name="Tags", value='`' + ", ".join(radio_data["tags"].split(",")) + '`', inline=False)
    embed.set_footer(text=radio_data["homepage"], icon_url=radio_data["favicon"])
    return embed


async def play_radio_stream(guild: Guild, radio_data):
    radio_channel = None
    for channel in guild.channels:
        if all([
            isinstance(channel, disnake.VoiceChannel),
            channel.name == "radio"
        ]):
            radio_channel = channel
            break
    if radio_channel is not None and isinstance(radio_channel, disnake.VoiceChannel):
        voice_client = guild.voice_client
        if voice_client is None:
            voice_client = await radio_channel.connect()
        if voice_client is not None and isinstance(voice_client, VoiceClient):
            if voice_client.is_playing():
                voice_client.stop()
            stream = get_radio_stream(radio_data["url_resolved"])
            voice_client.play(stream)
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
            stream.cleanup()
            voice_client.stop()


async def begin(ctx, stations):
    if stations is not None:
        station_names = set([station["name"] for station in stations if len(station["name"]) < 30])
        print(f"{len(station_names)} station names found", *[(name, len(name)) for name in station_names], sep="\n")
        select_options = create_select_option_list(station_names)
        view = SelectStationView(
            select_options,
            stations
        )
        select = await ctx.send(
            view=view
        )
        chosen = await view.get_results()
        await select.delete()
        await ctx.send(embed=now_playing_embed(chosen), delete_after=300)
        await play_radio_stream(ctx.guild, chosen)


class SelectStation(disnake.ui.Select):
    def __init__(self, options, stations):
        self.stations = {
            station['name']: station
            for station in stations
        }
        self.result = None
        super().__init__(placeholder="Select a station", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        while len(self.values) == 0:
            await asyncio.sleep(1)
        self.result = self.stations[self.values[0]]

    async def get_result(self):
        while self.result is None:
            await asyncio.sleep(1)
        return self.result


class SelectStationView(disnake.ui.View):
    def __init__(self, options, stations):
        super().__init__()
        self.add_item(SelectStation(options, stations))

    async def get_results(self):
        return await self.children[0].get_result()


class RadioStreamer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search_radio")
    # @commands.cooldown(1, 900, commands.BucketType.guild)
    async def radio_search(self, ctx: Context, *, query):
        await ctx.message.delete()
        stations = search_radio_channels("name", query)
        await begin(ctx, stations)

    @commands.command(name="stop_radio")
    # @commands.cooldown(1, 900, commands.BucketType.guild)
    async def stop_radio(self, ctx: Context):
        await ctx.message.delete()
        voice_client = ctx.guild.voice_client
        if voice_client is not None and isinstance(voice_client, VoiceClient):
            voice_client.stop()


def setup(bot):
    bot.add_cog(RadioStreamer(bot))
