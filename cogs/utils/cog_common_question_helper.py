from disnake.ext import commands
import aiosqlite


class CogCommonQuestionHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(self.bot.db) as db:
            async with db.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS common_questions (
                        id INTEGER,
                        question TEXT,
                        PRIMARY KEY (id)
                    )
                """)

                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS common_answers (
                        id INTEGER,
                        question_id INTEGER,
                        answer TEXT,
                        PRIMARY KEY (id),
                        FOREIGN KEY (question_id) REFERENCES common_questions(id)
                    )
                """)

                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS common_question_answers (
                        question_id INTEGER,
                        answer_id INTEGER,
                        PRIMARY KEY (question_id, answer_id),
                        FOREIGN KEY (question_id) REFERENCES common_questions(id),
                        FOREIGN KEY (answer_id) REFERENCES common_answers(id)
                    )
                """)

                await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if any([
            message.author.bot,
            message.content.startswith(self.bot.command_prefix),
            not message.channel.name.startswith('help')
        ]):
            return

        async with aiosqlite.connect(self.bot.db) as db:
            async with db.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, question FROM common_questions
                """)
                found = await cursor.fetchall()
                questions = {
                    question[0]: question[1] for question in found
                }

                distance = {
                    question_id: self.levenshtein(message.content, question)
                    for question_id, question in questions.items()
                }

                matching_question_ids = {}
                for question_id, question in questions.items():
                    qd = self.levenshtein(
                        message.content, question
                    )
                    if qd < 3:
                        matching_question_ids[question_id] = qd

                if len(matching_question_ids) == 0:
                    return

                question_id = min(matching_question_ids, key=matching_question_ids.get)

                await cursor.execute("""
                    SELECT answer FROM common_answers
                    WHERE question_id = ?
                """, (question_id,))
                found = await cursor.fetchall()
                answers = [answer[0] for answer in found]

                # send the answer
                await message.channel.send(
                    '\n'.join(answers)
                )

    @staticmethod
    def levenshtein(a, b):
        """Calculates the Levenshtein distance between two strings."""
        if a == b:
            return 0
        if len(a) == 0:
            return len(b)
        if len(b) == 0:
            return len(a)

        matrix = [list(range(len(b) + 1))]
        for i in range(1, len(a) + 1):
            matrix.append([i] + [0] * len(b))
            for j in range(1, len(b) + 1):
                deletion = matrix[i - 1][j] + 1
                insertion = matrix[i][j - 1] + 1
                substitution = matrix[i - 1][j - 1]
                if a[i - 1] != b[j - 1]:
                    substitution += 1
                matrix[i][j] = min(deletion, insertion, substitution)
        return matrix[-1][-1]


def setup(bot):
    bot.add_cog(CogCommonQuestionHelper(bot))
