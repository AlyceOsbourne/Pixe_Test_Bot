"""A pyston rest api powered code evaluator"""
from typing import Optional

from nextcord.ext import commands
from nextcord import File as NFile
from pyston import PystonClient, File


class CodeEval(commands.Cog, name="Code Evaluator"):

    @commands.command(name='eval', help='Evaluates code')
    async def eval(self, ctx, *, code):
        """Evaluates code
        Usage example:
        'bot_prefix eval
        ```python
        print("Hello World")
        ```
        """
        try:
            client = PystonClient()  # new client for each eval so no pollution
            lang, code = map(str.strip, code.strip('"\'`\n').split('\n', 1))
            if len(code) > 265:
                await ctx.send(f"""```{code[:50]}..\n. is too long```""")
                return

            output = await client.execute(lang, [File(code)])
            if output:
                await ctx.send(f'```\n{output}```')
            else:
                await ctx.send('```\nNo output```')
        except Exception as e:
            print(e)
            await ctx.send(f'```{e}```')

    @commands.command(name='find_py_docs', help='Uses eval to get the docs for a given module')
    async def find_docs(self, ctx, module, *, function: Optional[str] = None):

        python_versions = [
            '2.7',
            '3.6',
            '3.7',
            '3.8',
            '3.9',
            '3.10'
        ]

        # reply with a select menu of python versions

        client = PystonClient()
        file = f"""
import inspect

module = __import__('{module}')
docs = inspect.getdoc(module)"""
        if function:
            file += f"""\nif len('{function}') > 0:\n\tdocs = inspect.getdoc(getattr(module, '{function}'))
        """
        file += "\nprint(docs)"
        output = await client.execute('python', [File(file)])
        if output:
            # get the value from the output coroutine
            # if output is not None, send it
            if output:
                # convert the output to a string
                output = str(output)
                # if the output is too long, send it as a file
                if len(output) > 2000:
                    file = NFile(output)
                    await ctx.send(file=file)
                else:
                    await ctx.send(f"```\n{output}\n```")


def setup(bot):
    bot.add_cog(CodeEval())
