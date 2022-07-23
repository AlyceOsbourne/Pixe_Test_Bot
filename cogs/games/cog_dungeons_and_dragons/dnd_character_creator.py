# cog with commands to create a character and add it to the database
# players can have up to 5 characters
# each player can be the leader of up to 5 parties
# each player can be the leader of up to 1 faction
import asyncio
import json
from collections import namedtuple
from typing import Literal

import aiosqlite
import nextcord.ui
from nextcord import Member
from nextcord.ext import commands
from nextcord.ext.commands import Context

stat_names = [
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
    "hit_points",
    "proficiency_bonus"
]
skill_names = [
    "athletics",
    "acrobatics",
    "sleight_of_hand",
    "stealth",
    "arcana",
    "history",
    "investigation",
    "nature",
    "religion",
    "animal_handling",
    "insight",
    "medicine",
    "perception",
    "survival",
    "deception",
    "intimidation",
    "performance",
    "persuasion"
]

BaseStats = namedtuple("BaseStats", stat_names, defaults=(10,) * len(stat_names))
StatModifiers = namedtuple("StatModifiers", stat_names, defaults=(0,) * len(stat_names))
BaseSkills = namedtuple("BaseSkills", skill_names, defaults=(0,) * len(skill_names))
SkillModifiers = namedtuple("SkillModifiers", skill_names, defaults=(0,) * len(skill_names))

CombatClass = namedtuple("CombatClass", [
    "name",
    "hit_die",
    "saving_throws",
    "stat_modifiers",
    "skill_modifiers"
])

BaseInfo = namedtuple("BaseInfo", [
    "title",
    "forename",
    "middle_name",
    "surname",
    "nickname",
    "age",
    "gender",
    "bio"
])

CharacterRace = namedtuple("CharacterRace", [
    "name",
    "stat_modifiers",
    "skill_modifiers"
])

Alignment = Literal[
    "Chaotic Good",
    "Chaotic Evil",
    "Chaotic Neutral",
    "Neutral Good",
    "Neutral Evil",
    "True Neutral",
    "Lawful Good",
    "Lawful Evil",
    "Lawful Neutral"
]

Character = namedtuple("Character", [
    "base_info",
    "character_species",
    "base_stats",
    "base_skills",
    "combat_class",
    "alignment"
])


def character_to_json(character: Character):
    data = json.dumps(
        {
            key: value._asdict()
            if hasattr(value, "_asdict") else value
            for key, value in character._asdict().items()
        },
        indent=4
    )
    return data


def character_from_json(json_str):
    data = json.loads(json_str)
    data["base_info"] = BaseInfo(**data["base_info"])
    data["character_species"] = CharacterRace(**data["character_species"])
    data["base_stats"] = BaseStats(**data["base_stats"])
    data["base_skills"] = BaseSkills(**data["base_skills"])
    data["combat_class"] = CombatClass(**data["combat_class"])
    return Character(**data)


class DNDCharacterCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # on ready
    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect("pixie.sqlite") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS character_data (
                    character_id INTEGER,
                    character_data TEXT,
                    PRIMARY KEY (character_id),
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """)
            await db.commit()

    @staticmethod
    async def add_character(ctx: Context, character: Character):
        async with aiosqlite.connect("pixie.sqlite") as db:
            character_id = await db.execute("""
                SELECT last_insert_rowid()
            """)
            character_id = await character_id.fetchone()
            character_id = character_id[0]
            await db.execute("""
                INSERT INTO characters (
                    id, user_id
                ) VALUES (
                    ?,
                    ?
                )
            """, (character_id, ctx.author.id))
            await db.execute("""
                INSERT INTO character_data (
                    character_id,
                    character_data
                ) VALUES (
                    ?,
                    ?
                )
            """, (character_id, character_to_json(character)))

            await db.commit()

    @staticmethod
    async def character_count(ctx: Context):
        async with aiosqlite.connect("pixie.sqlite") as db:
            found = await db.execute("""
                SELECT COUNT(*) FROM characters WHERE user_id = ?
            """, (ctx.author.id,))
            found = await found.fetchone()
            return found[0]

    # get characters
    @staticmethod
    async def get_characters(ctx: Context):
        async with aiosqlite.connect("pixie.sqlite") as db:
            found = await db.execute("""
                SELECT character_data FROM character_data WHERE character_id IN (
                    SELECT id FROM characters WHERE user_id = ?
                )
            """, (ctx.author.id,))
            found = await found.fetchall()
            return [character_from_json(character[0]) for character in found]

    # delete character
    async def delete_character(self, ctx: Context):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute("""
                DELETE FROM characters WHERE user_id = ?
            """, (ctx.author.id,))
            await db.commit()

    # edit character
    async def edit_character(self, ctx: Context, character_id: int, character: Character):
        async with aiosqlite.connect(self.bot.db_path) as db:
            await db.execute("""
                UPDATE characters SET character_data = ? WHERE user_id = ? AND id = ?
            """, (character_to_json(character), ctx.author.id, character_id))
            await db.commit()

    async def get_base_info(self, ctx: Context):
        base_data = {}
        for question, key in [
            ("What is your title?", "title"),
            ("What is your forename?", "forename"),
            ("What is your middle name?", "middle_name"),
            ("What is your surname?", "surname"),
            ("What is your nickname?", "nickname"),
            ("What is your age?", "age"),
            ("What is your gender?", "gender"),
            ("Now, tell me a little about yourself?", "bio")
        ]:
            base_data[key] = None
            while base_data[key] is None:
                ask = await ctx.send(question)
                # await reply from user
                reply = await self.bot.wait_for("message", check=lambda m: all([
                    m.channel == ctx.channel,
                    m.author == ctx.author
                ]))
                answer = reply.content
                await reply.delete()
                await ask.edit(content=f"You said {answer}.\nIs this Correct?")
                reply = await self.bot.wait_for("message", check=lambda m: all([
                    m.channel == ctx.channel,
                    m.author == ctx.author
                ]))
                if reply.content.lower().startswith("y"):
                    base_data[key] = answer
                await ask.delete()
                await reply.delete()
        return BaseInfo(**base_data)

    async def get_character_species(self, ctx):
        species = {
            "dwarf": CharacterRace(
                name="Dwarf",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "elf": CharacterRace(
                name="Elf",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "halfling": CharacterRace(
                name="Halfling",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "human": CharacterRace(
                name="Human",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "orc": CharacterRace(
                name="Orc",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "tiefling": CharacterRace(
                name="Tiefling",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "half-elf": CharacterRace(
                name="Half-Elf",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "half-orc": CharacterRace(
                name="Half-Orc",
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            )
        }

        class SpeciesSelect(nextcord.ui.Select):
            options = [
                nextcord.SelectOption(
                    label=k,
                    value=k
                )
                for k
                in species
            ]

            def __init__(self):
                super().__init__(
                    min_values=1,
                    max_values=1,
                    options=self.options,
                )

            async def result(self):
                while len(self.values) < self.min_values:
                    await asyncio.sleep(0.1)
                return self.values[0]

        class SpeciesSelectView(nextcord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(SpeciesSelect())

            async def result(self):
                return await self.children[0].result()

        choice = None
        while choice is None:
            view = SpeciesSelectView()
            ask = await ctx.send("And what is your species?", view=view)
            selection = await view.result()
            view.stop()
            await ask.edit(content=f"You said {selection}.\nIs this correct?", view=None)
            reply = await self.bot.wait_for("message", check=lambda m: all([
                m.channel == ctx.channel,
                m.author == ctx.author
            ]))
            if reply.content.lower().startswith("y"):
                choice = species[selection]
            else:
                choice = None
            await ask.delete()
            await reply.delete()
        return choice

    async def get_combat_class(self, ctx: Context):
        classes = {
            "barbarian": CombatClass(
                name="Barbarian",
                hit_die="d12",
                saving_throws=[
                    "strength",
                    "constitution"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "bard": CombatClass(
                name="Bard",
                hit_die="d8",
                saving_throws=[
                    "dexterity",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "cleric": CombatClass(
                name="Cleric",
                hit_die="d8",
                saving_throws=[
                    "wisdom",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "druid": CombatClass(
                name="Druid",
                hit_die="d8",
                saving_throws=[
                    "wisdom",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "fighter": CombatClass(
                name="Fighter",
                hit_die="d10",
                saving_throws=[
                    "strength",
                    "constitution"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "monk": CombatClass(
                name="Monk",
                hit_die="d8",
                saving_throws=[
                    "dexterity",
                    "wisdom"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "paladin": CombatClass(
                name="Paladin",
                hit_die="d10",
                saving_throws=[
                    "wisdom",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "ranger": CombatClass(
                name="Ranger",
                hit_die="d10",
                saving_throws=[
                    "dexterity",
                    "wisdom"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "rogue": CombatClass(
                name="Rogue",
                hit_die="d8",
                saving_throws=[
                    "dexterity",
                    "intelligence"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "sorcerer": CombatClass(
                name="Sorcerer",
                hit_die="d6",
                saving_throws=[
                    "constitution",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "warlock": CombatClass(
                name="Warlock",
                hit_die="d8",
                saving_throws=[
                    "wisdom",
                    "charisma"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            ),
            "wizard": CombatClass(
                name="Wizard",
                hit_die="d6",
                saving_throws=[
                    "intelligence",
                    "wisdom"
                ],
                stat_modifiers=StatModifiers(*StatModifiers._field_defaults),
                skill_modifiers=SkillModifiers(*SkillModifiers._field_defaults)
            )
        }

        class CombatClassSelect(nextcord.ui.Select):

            options = [
                nextcord.SelectOption(
                    label=k,
                    value=k
                )
                for k
                in classes
            ]

            def __init__(self):
                super().__init__(
                    min_values=1,
                    max_values=1,
                    options=self.options,
                )

            async def result(self):
                while len(self.values) < self.min_values:
                    await asyncio.sleep(0.1)
                return self.values[0]

        class CombatClassSelectView(nextcord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(CombatClassSelect())

            async def result(self):
                return await self.children[0].result()

        choice = None
        while choice is None:
            view = CombatClassSelectView()
            ask = await ctx.send("And what is your combat class?", view=view)
            selection = await view.result()
            view.stop()
            await ask.edit(content=f"You said {selection}.\nIs this correct?", view=None)
            reply = await self.bot.wait_for("message", check=lambda m: all([
                m.channel == ctx.channel,
                m.author == ctx.author
            ]))
            if reply.content.lower().startswith("y"):
                choice = classes[selection]
            else:
                choice = None
            await ask.delete()
            await reply.delete()
        return choice

    async def get_alignment(self, ctx: Context):
        class AlignmentSelect(nextcord.ui.Select):
            options = [
                nextcord.SelectOption(
                    label="Lawful Good",
                    value="lawful good"
                ),
                nextcord.SelectOption(
                    label="Neutral Good",
                    value="neutral good"
                ),
                nextcord.SelectOption(
                    label="Chaotic Good",
                    value="chaotic good"
                ),
                nextcord.SelectOption(
                    label="Lawful Neutral",
                    value="lawful neutral"
                ),
                nextcord.SelectOption(
                    label="Neutral",
                    value="neutral"
                ),
                nextcord.SelectOption(
                    label="Chaotic Neutral",
                    value="chaotic neutral"
                ),
                nextcord.SelectOption(
                    label="Lawful Evil",
                    value="lawful evil"
                ),
                nextcord.SelectOption(
                    label="Neutral Evil",
                    value="neutral evil"
                ),
                nextcord.SelectOption(
                    label="Chaotic Evil",
                    value="chaotic evil"
                )
            ]

            def __init__(self):
                super().__init__(
                    min_values=1,
                    max_values=1,
                    options=self.options,
                )

            async def result(self):
                while len(self.values) < self.min_values:
                    await asyncio.sleep(0.1)
                return self.values[0]

        class AlignmentSelectView(nextcord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(AlignmentSelect())

            async def result(self):
                return await self.children[0].result()

        choice = None
        while choice is None:
            view = AlignmentSelectView()
            ask = await ctx.send("And what is your alignment?", view=view)
            selection = await view.result()
            view.stop()
            await ask.edit(content=f"You said {selection}.\nIs this correct?", view=None)
            reply = await self.bot.wait_for("message", check=lambda m: all([
                m.channel == ctx.channel,
                m.author == ctx.author
            ]))
            if reply.content.lower().startswith("y"):
                choice = selection
            else:
                await ask.delete()
                choice = None
            await ask.delete()
            await reply.delete()
        return choice

    @commands.command(name="create_character")
    async def create_character(self, ctx: Context):
        # a character creation process
        # we ask the user a series of questions to create a character
        # once complete we confirm the character, ask if they want to save it, and if they do we save it
        # if they don't we delete the character

        # get character count
        character_count = await self.character_count(ctx)
        if character_count >= 5:
            await ctx.send("You can only create 5 characters.")
            return

        # get base info
        base_info = await self.get_base_info(ctx)
        if base_info is None:
            return

        # get character species
        character_species = await self.get_character_species(ctx)
        if character_species is None:
            return

        # get base stats
        base_stats = BaseStats(**{field: 10 for field in BaseStats._fields})
        if base_stats is None:
            return

        base_skills = BaseSkills(**{field: 0 for field in BaseSkills._fields})
        if base_skills is None:
            return

        combat_class = await self.get_combat_class(ctx)
        if combat_class is None:
            return

        alignment = await self.get_alignment(ctx)
        if alignment is None:
            return

        character = Character(
            base_info=base_info,
            character_species=character_species,
            base_stats=base_stats,
            base_skills=base_skills,
            combat_class=combat_class,
            alignment=alignment
        )

        # confirm character
        prompt = await ctx.send(
            f'{character.base_info.title} {character.base_info.forename} {character.base_info.middle_name} {character.base_info.surname} the "{character.base_info.nickname}" is a  {alignment} {character.character_species.name} {combat_class.name}.'
        )
        ask = await ctx.send("Is this correct")
        reply = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        if reply.content.startswith("y"):
            # add character to database
            await self.add_character(ctx, character)
            await ctx.send("Character created.", delete_after=5)
        else:
            await ctx.send("Character creation cancelled.", delete_after=5)
        await ask.delete()
        await prompt.delete()
        await reply.delete()

    @commands.command(name="list_characters")
    async def list_characters(self, ctx: Context):
        # list all characters
        await ctx.message.delete()
        characters = await self.get_characters(ctx)
        if len(characters) == 0:
            await ctx.send("You have no characters.")
            return
        embed = nextcord.Embed(title="Characters")

        for i, character in enumerate(characters):
            embed.add_field(
                name=f"{i + 1}. {character.base_info.title} {character.base_info.forename} {character.base_info.middle_name} {character.base_info.surname}",
                value=f"A {character.base_info.gender} {character.alignment} {character.character_species.name} {character.combat_class.name}\n\n\"{character.base_info.nickname}\"\n\n\"*{character.base_info.bio}*\"",
                inline=False
            )
        auth: Member = ctx.author
        embed.set_footer(text=auth.name, icon_url=auth.display_avatar.url)
        await ctx.send("Your characters:\n", embed=embed)

        return characters
