# set up a basic db with users and guilds
from nextcord.ext import commands
import aiosqlite

table_creation_statements = {
    'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER,
                    user_id TEXT,
                    PRIMARY KEY (id)
                )
            """,
    'guilds': """
                CREATE TABLE IF NOT EXISTS guilds (
                    id INTEGER,
                    guild_id TEXT,
                    PRIMARY KEY (id)
                )
            """,
    'guild_members': """
                CREATE TABLE IF NOT EXISTS guild_members (
                    guild_id TEXT,
                    user_id TEXT,
                    PRIMARY KEY (guild_id, user_id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """
}


class PixieBotDB(commands.Cog, name="DB"):
    def __init__(self, bot):
        self.bot = bot

    # on ready create the db, adding each table if not exist
    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(self.bot.db) as db:
            for table_name in table_creation_statements:
                await db.execute(table_creation_statements[table_name])
            await db.commit()
            await self.populate_db()

    # populate the db with users and guilds
    async def populate_db(self):
        async with aiosqlite.connect(self.bot.db) as db:
            for guild in self.bot.guilds:
                # insert if not exist
                await db.execute("""
                    INSERT OR IGNORE INTO guilds (guild_id)
                    VALUES (?)
                """, (guild.id,))
                # commit changes
                await db.commit()
                # insert if not exist
                for member in guild.members:
                    await db.execute("""
                        INSERT OR IGNORE INTO users (user_id)
                        VALUES (?)
                    """, (member.id,))
                    await db.execute("""
                        INSERT OR IGNORE INTO guild_members (guild_id, user_id)
                        VALUES (?, ?)
                    """, (guild.id, member.id))
                    # commit changes
                    await db.commit()

    # on member join add user to db
    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id)
                VALUES (?)
            """, (member.id,))
            await db.commit()
            await db.execute("""
                INSERT OR IGNORE INTO guild_members (guild_id, user_id)
                VALUES (?, ?)
            """, (member.guild.id, member.id))
            await db.commit()

    # on member join add the user to the db
    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id)
                VALUES (?)
            """, (member.id,))
            await db.commit()
            await db.execute("""
                INSERT OR IGNORE INTO guild_members (guild_id, user_id)
                VALUES (?, ?)
            """, (member.guild.id, member.id))
            await db.commit()

    # on member leave remove the user from the db
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                DELETE FROM users WHERE user_id = ?
            """, (member.id,))
            await db.commit()
            await db.execute("""
                DELETE FROM guild_members WHERE user_id = ?
            """, (member.id,))
            await db.commit()

    # on guild join add the guild to the db
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                INSERT OR IGNORE INTO guilds (guild_id)
                VALUES (?)
            """, (guild.id,))
            await db.commit()
            # insert if not exist
            async for member in guild.members:
                await db.execute("""
                    INSERT OR IGNORE INTO users (user_id)
                    VALUES (?)
                """, (member.id,))
                await db.execute("""
                    INSERT OR IGNORE INTO guild_members (guild_id, user_id)
                    VALUES (?, ?)
                """, (guild.id, member.id))
                # commit changes
                await db.commit()

    # on guild leave remove the guild from the db
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # we need to remove the guild from the db, and all member who are only a part of this guild no other
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute("""
                DELETE FROM guilds WHERE guild_id = ?
            """, (guild.id,))
            await db.commit()
            await db.execute("""
                DELETE FROM guild_members WHERE guild_id = ?
            """, (guild.id,))
            await db.commit()
            # remove all users who are only in this guild
            await db.execute("""
                DELETE FROM users WHERE id NOT IN (SELECT user_id FROM guild_members)
            """)
            await db.commit()


def setup(bot):
    bot.add_cog(PixieBotDB(bot))
