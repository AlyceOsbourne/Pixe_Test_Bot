# adds tables to the pixie.sqlite db
import aiosqlite
from nextcord.ext import commands

character_tables = dict(
    characters="""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER AUTO_INCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    PRIMARY KEY (id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
    user_characters="""
                CREATE TABLE IF NOT EXISTS user_characters (
                    user_id TEXT,
                    character_id INTEGER,
                    PRIMARY KEY (user_id, character_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (character_id) REFERENCES characters (character_id)
                )
            """
)

party_tables = dict(
    party="""
                CREATE TABLE IF NOT EXISTS party (
                    id INTEGER UNIQUE,
                    leader_id TEXT,
                    PRIMARY KEY (id),
                    FOREIGN KEY (leader_id) REFERENCES users (user_id)
                )
            """,
    party_members="""
                CREATE TABLE IF NOT EXISTS party_characters (
                    party_id INTEGER,
                    character_id INTEGER,
                    PRIMARY KEY (party_id, character_id),
                    FOREIGN KEY (party_id) REFERENCES party (id),
                    FOREIGN KEY (character_id) REFERENCES characters (character_id)
                )
            """
)

faction_tables = dict(
    factions="""
                CREATE TABLE IF NOT EXISTS factions (
                    id INTEGER UNIQUE,
                    leader_id TEXT,
                    PRIMARY KEY (id),
                    FOREIGN KEY (leader_id) REFERENCES users (user_id)
                )
            """,
    faction_members="""
                CREATE TABLE IF NOT EXISTS faction_characters (
                    faction_id INTEGER,
                    character_id INTEGER,
                    PRIMARY KEY (faction_id, character_id),
                    FOREIGN KEY (faction_id) REFERENCES factions (id),
                    FOREIGN KEY (character_id) REFERENCES characters (character_id)
                )
            """
)


class DatabaseDND(commands.Cog, name="DND DB"):
    def __init__(self, bot):
        self.bot = bot

    # clean up the statements, as they have loads of \n and excess spaces etc
    create_table_statements = {
        key: value.replace("\n", "").replace("\t", "").replace("\r", "").replace("    ", "")
        for key, value in {
            **character_tables,
            **party_tables,
            **faction_tables
        }.items()
    }

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(self.bot.db) as db:
            for table_name in self.create_table_statements:
                try:
                    await db.execute(self.create_table_statements[table_name])
                except Exception as e:
                    print(table_name, self.create_table_statements[table_name], e, sep='\n')
