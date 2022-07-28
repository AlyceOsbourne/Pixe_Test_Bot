# moderator tools to provide people with warnings, and a ban tool that collect all of the user info, including
# their messages, and then ban them.
import time
from datetime import datetime, timedelta

import aiosqlite
import disnake
from disnake.ext import commands, tasks
import json


class ModTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # on ready create db for warns and ban data
    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    user_id TEXT, 
                    guild_id TEXT,
                    warn_reason TEXT,
                    warn_timestamp DATETIME,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.commit()
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ban_data (
                    user_id TEXT, /* discord user id */
                    guild_id TEXT, /* discord guild id */
                    reason TEXT, /* reason for ban */
                    ban_time DATETIME, /* time of ban */
                    ban_data TEXT, /* json of messages from user */
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.commit()
            self.remove_warns.start()

    @commands.command(name="warn", help="Warn a user", hidden=True)
    @commands.has_guild_permissions(ban_members=True)
    async def warn(self, ctx, user: disnake.Member, *, reason):
        async with aiosqlite.connect(self.bot.db) as db:
            async with db.cursor() as cursor:
                # add warn to db
                await cursor.execute("""
                    INSERT INTO warns (user_id, guild_id, warn_reason, warn_timestamp)
                    VALUES (?, ?, ?, ?)
                """, (user.id, ctx.guild.id, reason, datetime.utcnow()))
                await db.commit()
                num_warns = await cursor.execute("""
                    SELECT COUNT(*) FROM warns
                    WHERE user_id = ? AND guild_id = ?
                """, (user.id, ctx.guild.id))
                num_warns = await num_warns.fetchone()
                num_warns = num_warns[0]
                await ctx.send(f"{user.mention} has been warned for {reason}")
                if num_warns == 2:
                    await user.mute()
                elif num_warns == 3:
                    await self.ban_user(ctx, user, reason)

    @commands.command(name="ban", help="Ban a user", hidden=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban_user(self, ctx, user, reason):
        async with aiosqlite.connect(self.bot.db) as db:
            async with db.cursor() as cursor:
                messages = await user.history(after=datetime.utcnow() - timedelta(hours=48)).flatten()
                messages = json.dumps(messages)
                await cursor.execute("""
                    INSERT INTO ban_data (user_id, guild_id, reason, ban_time, ban_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (user.id, ctx.guild.id, reason, datetime.utcnow(), messages))
                # sweep user from messages db
                await cursor.execute("""
                    DELETE FROM messages
                    WHERE user_id = ? AND guild_id = ?
                """, (user.id, ctx.guild.id))
                await db.commit()
                await user.ban(reason=reason)
                # batch delete messages from server

        # sweep the users messages

    # loop to remove warns that are older than than 21 days
    @tasks.loop(hours=24)
    async def remove_warns(self):
        async with aiosqlite.connect(self.bot.db) as db:
            async with db.cursor() as cursor:
                await cursor.execute("""
                    DELETE FROM warns
                    WHERE warn_timestamp < ?
                """, (datetime.utcnow() - timedelta(days=21),))
                await db.commit()

    @remove_warns.before_loop
    async def before_remove_warns(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(ModTools(bot))
