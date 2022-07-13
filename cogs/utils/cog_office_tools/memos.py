import asyncio
import datetime
import os

import aiosqlite
import nextcord
from nextcord import Embed
from nextcord.ext import commands, application_checks


class MemoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.run(self.confirm_db())

    async def confirm_db(self):
        if not os.path.exists('memo.sqlite'):
            async with aiosqlite.connect('memo.sqlite') as db:
                # user table to store timezone
                await db.execute('''
                    CREATE TABLE memo (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        date TIMESTAMP NOT NULL,
                        author INTEGER NOT NULL
                    )
                ''')
                await db.commit()

    @commands.command(name='memo', aliases=['memo_add'])
    async def add_memo(self, ctx, title, *, memo):
        async with aiosqlite.connect('memo.sqlite') as db:
            await db.execute('''
                INSERT INTO memo (title, content, date, author)
                VALUES (?, ?, ?, ?)
            ''', (title, memo, datetime.datetime.now(), ctx.author.id))
            await db.commit()
            await ctx.send(f'Memo added!')

    # get memo
    @commands.command(name='memo_get')
    async def get_memo(self, ctx, title):
        async with aiosqlite.connect('memo.sqlite') as db:
            cursor = await db.execute('''
                SELECT * FROM memo WHERE title = ?
            ''', (title,))
            memo = await cursor.fetchone()
            if memo:
                embed = Embed(title=memo[1], description=memo[2], color=0x00ff00)
                embed.set_footer(text=f'Added by {self.bot.get_user(memo[3]).name}')
                await ctx.send(embed=embed)
            else:
                await ctx.send('Memo not found!')

    @commands.command(name='memo_list', aliases=['memo_ls'])
    async def list_memos(self, ctx):
        async with aiosqlite.connect('memo.sqlite') as db:
            cursor = await db.execute('''
                SELECT * FROM memo
            ''')
            memos = await cursor.fetchall()
            if memos:
                embed = Embed(title='Memos', color=0x00ff00)
                for memo in memos:
                    embed.add_field(name=memo[1], value=memo[2])
                await ctx.send(embed=embed)
            else:
                await ctx.send('No memos found!')

    @commands.command(name='memo_delete', aliases=['memo_del'])
    async def delete_memo(self, ctx, title):
        async with aiosqlite.connect('memo.sqlite') as db:
            await db.execute('''
                DELETE FROM memo WHERE title = ?
            ''', (title,))
            await db.commit()
            await ctx.send(f'Memo deleted!')

    @commands.command(name='memo_clear', aliases=['memo_clr'])
    @application_checks.is_owner()
    async def clear_memos(self, ctx):
        async with aiosqlite.connect('memo.sqlite') as db:
            await db.execute('''
                DELETE FROM memo
            ''')
            await db.commit()
            await ctx.send('Memos deleted!')

    @commands.command(name='memo_clear_user', aliases=['memo_clr_user'])
    @application_checks.is_owner()
    async def clear_memos_user(self, ctx, user: nextcord.User):
        async with aiosqlite.connect('memo.sqlite') as db:
            await db.execute('''
                DELETE FROM memo WHERE author = ?
            ''', (user.id,))
            await db.commit()
            await ctx.send(f'Memos deleted for {user.name}!')

    # clear before a date
    @commands.command(name='memo_clear_before', aliases=['memo_clr_before'])
    @application_checks.is_owner()
    async def clear_memos_before(self, ctx, date):
        async with aiosqlite.connect('memo.sqlite') as db:
            await db.execute('''
                DELETE FROM memo WHERE date < ?
            ''', (date,))
            await db.commit()
            await ctx.send(f'Memos deleted before {date}!')
