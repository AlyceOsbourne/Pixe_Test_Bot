"""Cog to play Hangman with the bot. gets random words from"""
import asyncio
from collections.abc import Iterable

import disnake
from disnake import Embed, Thread as TextThread
from disnake.ext import commands, tasks
from disnake.ext.commands import Context
from aiohttp import ClientSession
from asyncio import sleep, create_task

base_url = "https://random-words-api.vercel.app/word"

game_modes = {
    'default': '',
    'idioms': '/idiom',
    'vocab': '/vocabulary',
}


class HangManInstance:
    def __init__(self, word):

        self.word = word
        self.letters = set([letter for letter in word if letter.isalpha()])
        self.guessed_letters = set()
        self.available_letters = set(
            'abcdefghijklmnopqrstuvwxyz'
        )
        self.tries = 10

    def __str__(self):
        return ' '.join(
            # add letter if punctuation or space
            letter if not letter.isalpha() else
            '_' if letter not in self.guessed_letters else
            letter for letter in self.word
        )

    def guess(self, letter):
        state = 0
        if len(letter) == 1:
            if letter in self.letters and letter not in self.guessed_letters:
                self.available_letters.remove(letter)
                state = 1
            elif letter in self.guessed_letters:
                state = 0
            else:
                self.tries -= 1
                state = -1
            self.guessed_letters.add(letter)
            return state

    def is_over(self):
        return self.tries == 0 or self.guessed_letters == self.letters

    def is_won(self):
        return self.guessed_letters == self.letters

    def get_word(self):
        return self.word

    def get_tries(self):
        return self.tries

    def get_guessed_letters(self):
        return self.guessed_letters

    def get_available_letters(self):
        return self.available_letters

    async def update_game_embed(self, embed: Embed = Embed(title="Hangman")):

        embed.description = "`" + str(self) + "`"
        # delete all the fields

        embed.add_field(
            name='Tries',
            value=f'{"❌ " * self.tries}',
            inline=False
        )
        embed.add_field(
            name='Guessed letters',
            value=f'{", ".join(self.get_guessed_letters())}' if self.get_guessed_letters() else 'None',
            inline=False
        )
        embed.add_field(
            name='Available letters',
            value=f'{", ".join(sorted(self.get_available_letters()))}',
            inline=False
        )
        embed.set_footer(
            # guess a letter
            text=f'Guess a letter!`'
        )
        return embed


class HangMan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hangman', help=f"play hangman with the bot, game modes are {', '.join(game_modes.keys())}")
    async def hangman(self, ctx: Context, *, game_mode: str = 'default'):
        # create a new game
        await ctx.message.delete()
        async with ClientSession() as session:
            async with session.get(f'{base_url}{game_modes[game_mode]}') as resp:
                reply = await resp.json()
                reply = dict(*reply)
                word = reply['word'].lower()
                description = reply['definition']
                print(word, description, sep='\n')
        game = HangManInstance(word)
        print(game)
        embed = await game.update_game_embed()
        current = await ctx.send(embed=embed)
        while not game.is_over():
            try:
                guess = await ctx.bot.wait_for(
                    'message',
                    check=lambda m: all(
                        [
                            m.author == ctx.author,
                            m.channel == ctx.channel,
                            len(m.content) == 1,
                            m.content.isalpha(),
                        ],
                    ),
                    timeout=600
                )
            except asyncio.TimeoutError:
                await ctx.send('Timed out!')
                break
            else:
                result = game.guess(guess.content.lower())
                await guess.delete()

            embed = await game.update_game_embed(Embed(title="Hangman"))
            current = await current.edit(embed=embed)

            if game.is_over():
                current = await current.edit(
                    embed=Embed(
                        title="Hangman",
                        description=f"`{'You Won!' if game.is_won() else 'You Lose'}\n\n`{game.get_word()}`\n`{description}`\nCompleted with `{game.get_tries()}` tries remaining!\n`",
                        color=0x00ff00 if game.is_won() else 0xFF0000
                    )
                )
                await current.delete(delay=300)
                break
            if result == 1:
                await ctx.send('Correct!', delete_after=5)
            elif result == 0:
                await ctx.send('Already guessed!', delete_after=5)
            elif result == -1:
                await ctx.send('Wrong!', delete_after=5)
                await ctx.send(f'You have {game.get_tries()} tries left!', delete_after=5)


def setup(bot):
    bot.add_cog(HangMan(bot))
