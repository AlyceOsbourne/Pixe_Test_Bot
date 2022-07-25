import disnake
from disnake.ext import commands
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from requests_html import HTMLSession


class Search(commands.Cog, name='Search'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='search articles in pythonprogramming.net')
    async def search_articles(self, ctx):
        site_prefix = 'https://pythonprogramming.net'
        tseries_xpath = "//div[@class='card-panel hoverable']/a[@href]"
        tspecific_xpath = "//div[@class='collection']/a[@href]"

        begin = ctx.message.content.find('(')
        end = ctx.message.content.find(')')
        # remove ' (" ' and ' ") '
        term = ctx.message.content[begin + 2:end - 1]
        topic = term.replace(" ", "%20")
        search_link = f'{site_prefix}/search/?q={topic}'

        loop = asyncio.get_running_loop()
        session = HTMLSession()
        with ThreadPoolExecutor() as pool:
            resp = await loop.run_in_executor(pool, partial(session.get, search_link))

        await ctx.send('\n'.join([
            '```',
            'Tutorial Series:',
            *(f'  {site_prefix}{elem.links.pop()}' for elem in resp.html.xpath(tseries_xpath)),
            '```'
            '```',
            'Specific Articles:',
            *(f'  {site_prefix}{elem.links.pop()}' for elem in resp.html.xpath(tspecific_xpath)),
            '```'
        ]))


def setup(bot):
    bot.add_cog(Search(bot))
