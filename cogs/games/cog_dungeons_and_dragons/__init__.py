from cogs.games.cog_dungeons_and_dragons import databasednd, dnd_character_creator


def setup(bot):
    bot.add_cog(databasednd.DatabaseDND(bot))
    bot.add_cog(dnd_character_creator.DNDCharacterCreator(bot))
