import logging
import disnake
from disnake.ext import commands, tasks

from cogs.database.cog_db.db_functions import *


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Database cog loaded')

    def cog_unload(self):
        session.close()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('Database cog ready')
        for guild in self.bot.guilds:
            await add_guild(guild)

    # joins for various metrics
    # top users for given channel, returns a dict of discord users and their counts
    async def top_users_for_channel(self, channel, limit=5):
        query = session.query(Message.author_id, func.count(Message.author_id)).filter(
            Message.channel_id == channel.id).group_by(Message.author_id).order_by(func.count(Message.author_id).desc())
        return {user.as_disnake_user(self.bot): count for user, count in query.limit(limit)}

    # add events to add data to db

    # on join
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await add_guild_member(member.guild, member)

    # on leave
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await remove_guild_member(member)

    # on message
    @commands.Cog.listener()
    async def on_message(self, message):
        await add_message(message.channel, message)

    # on delete
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await delete_message(message)

    # on channel create
    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        await add_channel(channel, channel.guild)

    # on channel delete
    @commands.Cog.listener()
    async def on_channel_delete(self, channel):
        await remove_channel(channel)

    # on role create
    @commands.Cog.listener()
    async def on_role_create(self, role):
        await add_role(role.guild, role)

    # on role delete
    @commands.Cog.listener()
    async def on_role_delete(self, role):
        await remove_role(role.guild, role)

    # on guild create
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await add_guild(guild)

    # on guild delete
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await remove_guild(guild, guild.default_role)

    # task to add user activity to db
    @tasks.loop(seconds=60)
    async def add_user_activity(self):
        for guild in self.bot.guilds:
            online, idle, offline = 0, 0, 0
            for member in guild.members:
                if member.status in [disnake.Status.online]:
                    online += 1
                elif member.status in [disnake.Status.idle, disnake.Status.dnd, disnake.Status.do_not_disturb]:
                    idle += 1
                else:
                    offline += 1
            session.merge(GuildMemberActivity(guild_id=guild.id, online=online, idle=idle, offline=offline))


def setup(bot):
    bot.add_cog(Database(bot))
