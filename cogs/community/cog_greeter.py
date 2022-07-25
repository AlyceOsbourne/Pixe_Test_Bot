# cog that greets new members, and replies hello member if the bot is mentioned
import random

from disnake.ext import commands

# random greeting messages
greetings = [
    'Hello {0.mention}',
    'Hi {0.mention}',
    'Hey {0.mention}',
    'Howdy {0.mention}',
    'Greetings {0.mention}',
    'Salutations {0.mention}',
    'Welcome {0.mention}',
    'How are you {0.mention}',
    'How are you doing {0.mention}',
    'How are you doing today {0.mention}',
    'How are you doing? {0.mention}',
    'How are you? {0.mention}',
    'How are you doing? {0.mention}'
]
tutorial_messages = [
    ", please use {0}.commands() to get help",
    ", just so you know, you can use the {0}.commands() command to get help"
]


class Greeter(commands.Cog, name='Greeter'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send(
            random.choice(greetings).format(member) + random.choice(tutorial_messages).format(self.bot.command_prefix))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user:
            if message.content.startswith(self.bot.command_prefix):
                return
            if message.content.startswith(self.bot.user.mention):
                await message.channel.send(
                    random.choice(greetings).format(message.author) + random.choice(tutorial_messages).format(
                        self.bot.command_prefix))


def setup(bot):
    bot.add_cog(Greeter(bot))
