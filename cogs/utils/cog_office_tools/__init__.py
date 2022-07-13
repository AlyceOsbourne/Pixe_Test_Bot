"""Cog to handle memos, notes, reminders, etc."""
from cogs.utils.cog_office_tools.memos import MemoCog
from cogs.utils.cog_office_tools.reminder import ReminderCog


def setup(bot):
    bot.add_cog(MemoCog(bot))
    bot.add_cog(ReminderCog(bot))
