from datetime import timedelta, datetime

import disnake
from sqlalchemy import func

from cogs.database.cog_db.db_bases import *


async def add_guild(guild):
    session.merge(Guild(id=guild.id))
    for role in guild.roles:
        await add_role(guild, role)
    for channel in guild.channels:
        await add_channel(channel, guild)
    for member in guild.members:
        await add_guild_member(guild, member)


async def remove_guild(guild, role):
    session.delete(Guild(id=guild.id))
    session.delete(GuildRole(id=role.id, guild_id=guild.id))
    for member in guild.members:
        await remove_guild_member(member)
        # if member is not in any guilds delete the user
        if not session.query(GuildUser).filter(GuildUser.id == member.id).first():
            await remove_user(member)


async def add_user(member):
    session.merge(User(id=member.id))


async def remove_user(member):
    session.delete(User(id=member.id))


async def add_guild_member(guild, member):
    session.merge(GuildUser(user_id=member.id, guild_id=guild.id))


async def remove_guild_member(member):
    session.delete(GuildUser(id=member.id))


async def add_channel(channel, guild):
    session.merge(Channel(id=channel.id, guild_id=guild.id))
    if isinstance(channel, disnake.TextChannel) or isinstance(channel, disnake.VoiceChannel):
        for message in await channel.history(after=datetime.now() - timedelta(days=21)).flatten():
            await add_message(channel, message)


async def remove_channel(channel):
    session.delete(Channel(id=channel.id))


async def add_message(channel, message):
    session.merge(Message(id=message.id, channel_id=channel.id))


async def delete_message(message):
    session.delete(Message(id=message.id))


async def add_role(guild, role):
    session.merge(GuildRole(id=role.id, guild_id=guild.id))


async def remove_role(guild, role):
    session.delete(GuildRole(id=role.id, guild_id=guild.id))


async def most_frequent_users_channels(*channels, limit=5):
    query = session.query(Message.author_id, func.count(Message.author_id)).filter(
        Message.channel_id.in_([channel.id for channel in channels])).group_by(Message.author_id).order_by(
        func.count(Message.author_id).desc())
    return {user: count for user, count in query.limit(limit)}


async def get_guild_user_activity(guild, time: timedelta):
    query = session.query(GuildMemberActivity).filter(
        GuildMemberActivity.guild_id == guild.id).filter(
        GuildMemberActivity.activity_time > datetime.now() - time) \
        .order_by(GuildMemberActivity.activity_time.desc())
    return query.all()


__all__ = [
    'add_guild',
    'remove_guild',
    'add_user',
    'remove_user',
    'add_guild_member',
    'remove_guild_member',
    'add_channel',
    'remove_channel',
    'add_message',
    'delete_message',
    'add_role',
    'remove_role',
    'most_frequent_users_channels',
    'get_guild_user_activity',
    'session',
    *get_bases()
]
