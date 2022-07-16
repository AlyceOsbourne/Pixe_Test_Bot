"""cog to play the classic board game Mastermind is discord using buttons and emojis"""
import random
import nextcord.ext.commands as commands
import nextcord.ext.tasks as tasks
import nextcord.ui as ui
import nextcord.ext.application_checks as application_checks
from nextcord import Embed

EMOJIS = {
    'blue': '\u2b1e',
    'green': '\u2b1f',
    'red': '\u2b20',
    'yellow': '\u2b21'
}

# black unicode for empty
EMPTY = '\u2b22'

ROW_LENGTH = 4
NUM_TURNS = 10


class Mastermind(commands.Cog):
    # is instance based, so we can use it in multiple commands
    class MastermindInstance:
        def __init__(self):
            self.code = list(EMOJIS)
            random.shuffle(self.code)
            self.turns = NUM_TURNS
            self.guess = []
            self.previous_guessed = []

        def get_code(self):
            return self.code

        def get_turns(self):
            return self.turns

        def set_add_to_guess(self, emoji):
            if emoji not in self.guess:
                self.guess.append(emoji)
                return True
            return False

        def reset_guess(self):
            self.guess = []

        def confirm_guess(self):
            self.previous_guessed = self.guess
            self.guess = []
            self.turns -= 1

        def game_over(self):
            return self.turns == 0 or self.guess == self.code

        def did_win(self):
            return self.guess == self.code

        def get_guess_str(self):
            guess_str = []
            for i in range(len(self.guess)):
                guess_str.append(self.guess[i])
            for i in range(len(self.guess), ROW_LENGTH):
                guess_str.append(EMPTY)
            return ' '.join(guess_str)

        def get_code_str(self):
            return ' '.join(self.code)
