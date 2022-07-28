import disnake
from disnake.ext import commands
import os
import random

guild_id = 988202173152260176


class ServerBot_Control(commands.Cog, name='Cog_Control'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.vanity_roles = [
            
        ]

    @commands.command(help="get all the members' status")
    async def members_status(self, ctx):
        idle, online, offline = 0, 0, 0
        for member in ctx.guild.members:
            if member.status == disnake.Status.online:
                online += 1
            elif member.status == disnake.Status.offline:
                offline += 1
            else:
                idle += 1

        await ctx.send('\n'.join([
            '```',
            f'Member_Count: {ctx.guild.member_count},',
            f'Idle/DND: {idle},',
            f'Online:   {online},',
            f'Offline:  {offline}'
            '```']))

    @commands.command(help='Get info about bot commands')
    async def all_cmds(self, ctx):
        await ctx.send('\n'.join([
            '```',
            *(f'{cmd.name + ":": <17}{cmd.help}' for cmd in self.bot.commands),
            '```']))

    @commands.command(help='Reload all the cogs')
    async def reload_cogs(self, ctx):
        reloaded = []
        no_error = True
        for file in os.listdir('cogs'):
            if file.endswith('_cog.py'):
                cog_name = 'cogs.' + file[:-3]
                try:
                    self.bot.reload_extension(cog_name)
                except disnake.DiscordException as e:
                    no_error = False
                    await ctx.send('\n'.join(['```', f'{e}', '```']))

                reloaded.append((file[:-3], no_error))
                no_error = True

        await ctx.send('\n'.join([
            '```',
            'Reloaded Cogs:',
            *(f'  {"[PASS] " if no_err else "[FAIL] "}{name[:-4]}' for name, no_err in reloaded),
            '```']))

    @commands.Cog.listener()
    async def on_message(self, msg):
        cmd_list = [f'{self.bot.command_prefix}{cmd.name}' for cmd in self.bot.commands]
        if msg.author.bot or (msg.content in cmd_list) or len(msg.content) == 0: return

        guild = self.bot.get_guild(guild_id)
        author = msg.author

        if random.randint(1, 100) == 57:
            already_given = [role for role in author.roles if role.id in self.vanity_roles]

            if not already_given:
                role_id = random.choice(self.vanity_roles)
                role = guild.get_role(role_id)

                await author.add_roles(role)


def setup(bot):
    bot.add_cog(ServerBot_Control(bot))
