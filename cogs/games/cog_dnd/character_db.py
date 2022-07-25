# sqlalchemy character database
import sqlalchemy as sa
import sqlalchemy.orm as orm

from disnake.ext import commands, tasks

Base = orm.declarative_base()


# species table
class Entity(Base):
    __tablename__ = "entities"
    id = sa.Column(sa.Integer, primary_key=True)
