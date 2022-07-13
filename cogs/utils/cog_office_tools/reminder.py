import asyncio
import datetime
import os
import random

import aiosqlite
import dateutil.parser as dps
import pytz
from nextcord import Embed
from nextcord.ext import commands, tasks
from nextcord.ext.commands import Context

time_stamp_format_string = '%Y-%m-%d %H:%M:%S%z'


class ReminderCog(commands.Cog):
    """Cog that sets up a reminder, and reminds the user at the specified time"""

    def __init__(self, bot):
        self.bot = bot

    # on ready
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        await self.confirm_db()
        self.check_reminders.start()

    @staticmethod
    async def confirm_db():
        if not os.path.exists('reminder.sqlite'):
            # cols: id, title, description, created_at, author, reminder_at
            async with aiosqlite.connect('reminder.sqlite') as db:
                # reminder table
                # id integer primary key
                # title text
                # description text
                # created_at timestamp
                # reminder_at timestamp
                # author foreign key references users(id)
                # with foreign key to get auther and timezone
                await db.execute('''
                    CREATE TABLE reminder (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL,
                    author INTEGER NOT NULL,
                    reminder_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(author) REFERENCES users(id)
                    );
                ''')
                await db.execute('''
                    CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    timezone TEXT NOT NULL
                    );
                ''')
                await db.commit()
                await db.commit()

    async def get_description(self, ctx):
        try:
            ask = await ctx.send('Please enter the description of the reminder')
            description_reply = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
            description = description_reply.content
            await ask.delete()
            await description_reply.delete()
        except asyncio.TimeoutError:
            await ctx.send('Timed out!')
            return None
        return description

    @staticmethod
    async def get_time(ctx):
        try:
            ask = await ctx.send(f'When do you want to be reminded? (e.g. "tomorrow at 12:00")')
            time_reply = await ctx.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60
            )
            time = dps.parse(time_reply.content, fuzzy=True)
            # if time is older than now, raise error
            if time < datetime.datetime.now():
                raise ValueError
            await ask.delete()
            await time_reply.delete()
        except ValueError:
            await ctx.send('Invalid time!', delete_after=20)
            return
        except asyncio.TimeoutError:
            await ctx.send('Timed out!', delete_after=20)
            return
        # as utc time
        return time.astimezone(pytz.utc)

    async def get_timezone(self, ctx):
        try:
            async with aiosqlite.connect('reminder.sqlite') as db:
                # from users table get the TZ
                cursor = await db.execute('''
                    SELECT timezone FROM users WHERE discord_id = ?
                    ''', (ctx.author.id,))
                timezone = await cursor.fetchone()
                if timezone is not None:
                    timezone = timezone[0]
                    if timezone not in pytz.all_timezones:
                        timezone = None
            if timezone:
                # remind user of their TZ, and ask if they want to change it with timout of 30 seconds
                embed = Embed(title='Your timezone', color=0x00ff00)
                embed.add_field(name='Your timezone', value=timezone)
                embed.add_field(name='Do you want to change it?', value='Yes or No')
                ask = await ctx.send(embed=embed)
                try:
                    timezone_reply = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == ctx.author,
                        timeout=30)

                    if timezone_reply.content.lower().startswith('y'):
                        await timezone_reply.delete()
                        await ask.delete()
                        timezone = None
                        async with aiosqlite.connect('reminder.sqlite') as db:
                            await db.execute('''
                                DELETE FROM users WHERE discord_id = ?
                                ''', (ctx.author.id,))
                            await db.commit()
                    await timezone_reply.delete()
                except asyncio.TimeoutError:
                    pass
                await ask.delete()
            if not timezone:
                # ask for TZ
                embed = Embed(title='Set your timezone', color=0x00ff00)
                embed.add_field(name='Please enter your timezone', value='e.g. "America/New_York"')
                # add list of common timezones
                embed.add_field(name='Common timezones', value='\n'.join(random.sample(pytz.common_timezones, 25)))
                ask = await ctx.send(embed=embed)
                timezone_reply = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
                timezone = timezone_reply.content
                await ask.delete()
                await timezone_reply.delete()
                if timezone not in pytz.common_timezones:
                    await ctx.send('Invalid timezone!')
                    return None
                async with aiosqlite.connect('reminder.sqlite') as db:
                    await db.execute('''
                        INSERT INTO users (discord_id, timezone) VALUES (?, ?)
                        ''', (ctx.author.id, timezone))
                    await db.commit()
        except asyncio.TimeoutError:
            await ctx.send('Timed out!')
            return None
        return pytz.timezone(timezone)

    # add reminder
    @commands.command(name='reminder', aliases=['reminder_add'])
    async def add_reminder(self, ctx: Context, *, title):
        await ctx.message.delete()
        current_question_retries = 0
        description = None
        while description is None and current_question_retries < 3:
            description = await self.get_description(ctx)
            current_question_retries += 1
        current_question_retries = 0
        time = None
        while time is None and current_question_retries < 3:
            time = await self.get_time(ctx)
            current_question_retries += 1
        current_question_retries = 0
        tz = None
        while tz is None and current_question_retries < 3:
            tz = await self.get_timezone(ctx)
            current_question_retries += 1
        if time is None or tz is None:
            await ctx.send('Timed out!')
            return
        async with aiosqlite.connect('reminder.sqlite') as db:
            # now as utc
            await db.execute('''
                INSERT INTO reminder (title, description, created_at, author, reminder_at) VALUES (?, ?, ?, ?, ?)
                ''', (title, description, datetime.datetime.now(), ctx.author.id, time))
            await db.commit()
            embed = Embed(title=title, description=description, color=0x00ff00)
            embed.add_field(name='Created at', value=datetime.datetime.now().strftime(time_stamp_format_string),
                            inline=False)
            embed.add_field(name='Reminder at', value=time, inline=False)
            await ctx.send(embed=embed, delete_after=60)

    @commands.command(name='reminder_list', aliases=['reminder_ls'])
    async def list_reminders(self, ctx):
        async with aiosqlite.connect('reminder.sqlite') as db:
            cursor = await db.execute('''
                SELECT * FROM reminder WHERE author = ?
                ''', (ctx.author.id,))
            reminders = await cursor.fetchall()
            if reminders:
                embed = Embed(title='Reminders', color=0x00ff00)
                for reminder in reminders:
                    embed.add_field(name=reminder[1], value=reminder[2])
                await ctx.send(embed=embed)
            else:
                await ctx.send('No reminders found!')

    @commands.command(name='reminder_delete', aliases=['reminder_del'])
    async def delete_reminder(self, ctx, title):
        async with aiosqlite.connect('reminder.sqlite') as db:
            # get reminder from title
            cursor = await db.execute('''
                SELECT * FROM reminder WHERE title = ?
                ''', (title,))
            reminder = await cursor.fetchone()
            allow_delete = reminder[3] == ctx.author.id or ctx.author.guild_permissions.administrator
            if allow_delete:
                await db.execute('''
                    DELETE FROM reminder WHERE title = ?
                    ''', (title,))
                await db.commit()
                await ctx.send(f'Reminder "{title}" deleted!')

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        async with aiosqlite.connect('reminder.sqlite') as db:
            db.row_factory = aiosqlite.Row
            # we need the reminders and the timezones
            # we only want a maximum of 10 messages, sorted by reminder_at, and only reminders that are due
            cursor = await db.execute('''
                SELECT * FROM reminder
                LEFT JOIN users ON reminder.author = users.discord_id
                ORDER BY reminder_at ASC
                ''')
            reminders = await cursor.fetchall()
            for reminder in reminders:
                timezone = reminder['timezone']
                timezone_obj = pytz.timezone(timezone)
                remind_at = reminder['reminder_at']
                remind_at_obj = datetime.datetime.strptime(remind_at, time_stamp_format_string)
                remind_at_ufc_offsets = remind_at_obj.replace(tzinfo=timezone_obj)
                now = datetime.datetime.now()
                now_ufc_offsets = now.replace(tzinfo=pytz.utc)

                # account for DST
                if now_ufc_offsets.dst() != remind_at_ufc_offsets.dst():
                    if now_ufc_offsets.dst():
                        now_ufc_offsets += datetime.timedelta(hours=1)
                    else:
                        now_ufc_offsets -= datetime.timedelta(hours=1)

                if now_ufc_offsets >= remind_at_ufc_offsets:
                    # send reminder
                    embed = Embed(title=reminder['title'], description=reminder['description'], color=0x00ff00)
                    # dm
                    await self.bot.get_user(reminder['author']).send("Here is your reminder:", embed=embed)
                    # delete reminder
                    await db.execute('''
                        DELETE FROM reminder WHERE title = ?
                        ''', (reminder['title'],))
                    await db.commit()
