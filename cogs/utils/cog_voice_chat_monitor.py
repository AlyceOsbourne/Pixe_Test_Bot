# The bot should react to people joining voice channels, all except for the AFK channel. The bot should monitor all
# of the VC channels together counting a total number of people in them.
#
# There should be 2 additional channels,
# called vc_notification_1 and vc_notification_2.
#
# Whenever total number of people in the voice channels changes from
# 0 to 1 and stays greater than zero for at least a minute (to exclude people joining and leaving randomly),
# the bot should put a message inside of the vc_notification_1 with something like @ everyone, @ username joined the
# channel_name VC channel.

# Whenever total number if people in the voice channels changes from <2 to 2 and stays
# greater than zero for at least a minute, the bot should put a message inside of the vc_notification_2 with
# something like @ everyone, @ username1 and @ username2 joined the channel_name VC channel. To not trigger these
# messages when people are joining and leaving, for example when there's a party of 1 and the second person joins,
# then leaves, then another one joins and leaves then yet another does the same, there should be a timeout of 15
# minutes between subsequent messages posted to both channels.
# Alternatively maybe a message can be still posted but
# without pinking @ everyone, I'm not sure yet. Now, these 2 channels are going to be hidden by default and only
# available to people with the vc1_notification and vc2_notification roles. Sentdebot should react to 3 commands: -
# !vcnotification 1 - adds vc1_notification role to the user invoking it - !vcnotification 2 - adds vc2_notification
# - !vcnotification off - removes both roles I'm not sure if anyone would benefit from having both of these roles.
# Maybe? Maybe add !vcnotification 12 or !vcnotification 3 or !vcnotification 1+2 or something like this?
import time

import nextcord
from discord.ext import commands
from nextcord.ext import tasks


class VCMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currently_occupied_channels = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            role_names = [role.name for role in guild.roles]
            for role_name in ["vc1_notification", "vc2_notification"]:
                if role_name not in role_names:
                    await guild.create_role(name=role_name)
            channel_names = [channel.name for channel in guild.channels]
            for channel_name in ["vc_notification_1", "vc_notification_2"]:
                if channel_name not in channel_names:
                    channel = await guild.create_text_channel(channel_name)
                    await channel.set_permissions(guild.default_role, read_messages=False)
                    for role in guild.roles:
                        if role.name in ["vc1_notification", "vc2_notification"]:
                            await channel.set_permissions(role, read_messages=True)
        self.loop_vc_monitor.start()

    @tasks.loop(seconds=5)
    async def loop_vc_monitor(self):
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, nextcord.VoiceChannel):
                    if channel.id not in self.currently_occupied_channels and len(channel.members) > 0:
                        self.currently_occupied_channels[channel.id] = {
                            "members": [(member, time.time()) for member in channel.members],
                            # list of tuples of user and how long they've been in the channel
                            "sent_searching_for_people_message": (False, 0),  # state, time of last message
                            "sent_people_found_message": (False, 0),  # state, time of last message
                            "last_check_time": time.time()  # time of last check
                        }

                    elif channel.id in self.currently_occupied_channels:
                        if len(channel.members) == 0:
                            del self.currently_occupied_channels[channel.id]
                        elif len(channel.members) == 1:
                            if not channel.members[0] in self.currently_occupied_channels[channel.id]["members"]:
                                self.currently_occupied_channels[channel.id]["members"].append(
                                    (channel.members[0], time.time()))

                            elif time.time() - self.currently_occupied_channels[channel.id]["last_check_time"] > 60:
                                if not \
                                        self.currently_occupied_channels[channel.id][
                                            "sent_searching_for_people_message"][0]:
                                    notification_channel = self.bot.get_channel(guild.id, "vc_notification_1")
                                    await notification_channel.send(
                                        f"@ everyone, @ {channel.members[0].name} joined the {channel.name} VC channel")
                                    self.currently_occupied_channels[channel.id][
                                        "sent_searching_for_people_message"] = (True, time.time())
                                self.currently_occupied_channels[channel.id]["last_check_time"] = time.time()


                        elif len(channel.members) > 1:
                            if time.time() - self.currently_occupied_channels[channel.id]["last_check_time"] > 60:
                                if not self.currently_occupied_channels[channel.id]["sent_people_found_message"][0]:
                                    notification_channel = self.bot.get_channel(guild.id, "vc_notification_2")
                                    await notification_channel.send(
                                        f"@everyone, @{' @'.join([member.name for member in channel.members])} joined the {channel.name} VC channel")
                                    self.currently_occupied_channels[channel.id]["sent_people_found_message"] = (
                                        True, time.time())
                                self.currently_occupied_channels[channel.id]["last_check_time"] = time.time()
                        else:
                            self.currently_occupied_channels[channel.id]["last_check_time"] = time.time()


def setup(bot):
    bot.add_cog(VCMonitor(bot))
