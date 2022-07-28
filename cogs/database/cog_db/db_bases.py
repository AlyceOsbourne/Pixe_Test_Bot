import json
import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, create_engine, VARCHAR, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
import zlib

load_dotenv()
Base = declarative_base()


class Guild(Base):
    __tablename__ = "guilds"
    id = Column(String(30), primary_key=True)


class GuildPrefix(Base):
    __tablename__ = "guild_prefixes"
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    prefix = Column(String(30))


class User(Base):
    __tablename__ = "users"
    id = Column(String(30), primary_key=True)


class GuildUser(Base):
    __tablename__ = "guild_users"
    user_id = Column(String(30), ForeignKey('users.id'), primary_key=True)


class Channel(Base):
    __tablename__ = "channels"
    id = Column(String(30), primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    guild = relationship(Guild, backref='channels')


class Message(Base):
    __tablename__ = "messages"
    id = Column(String(30), primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship(Channel, backref='messages')
    timestamp = Column(DateTime, default=datetime.utcnow)


class Command(Base):
    __tablename__ = "commands"
    id = Column(String(100), unique=True, primary_key=True)
    description = Column(VARCHAR(256))
    usage = Column(VARCHAR(256))


class GuildCommand(Base):
    __tablename__ = "guild_commands"
    command_id = Column(String, ForeignKey('commands.id'), primary_key=True)
    guild_id = Column(String, ForeignKey('guilds.id'), primary_key=True)
    enabled = Column(Boolean)
    roles = Column(VARCHAR)
    role_blacklist = Column(Boolean)  # else whitelist


class GuildRole(Base):
    __tablename__ = "guild_roles"
    id = Column(String(30), primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    guild = relationship(Guild, backref='roles')
    vanity_role = Column(Boolean, default=False, nullable=False)


class GuildMemberActivity(Base):
    __tablename__ = "guild_member_activities"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Integer)
    idle = Column(Integer)
    offline = Column(Integer)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    guild = relationship(Guild)


class GuildMemberActivityGraph(Base):
    __tablename__ = "guild_member_activity_graph"
    id = Column(String, ForeignKey('guild_member_activities.id'), primary_key=True)
    image = Column(BLOB)


if __name__ == "__main__":
    engine = create_engine(url="sqlite:///:memory:", echo=True)
    Base.metadata.create_all(bind=engine)
    if input("Do you wish to save this database to file? [y/n] ").startswith('y'):
        engine.dispose()
        engine = create_engine(os.environ['DATABASE_URL'], echo=False)
        Base.metadata.create_all(bind=engine)
        print("Database saved to file.")
else:
    # if is imported
    engine = create_engine(
        os.environ['DATABASE_URL'],
        echo=True,
        json_serializer=json.dumps,
        json_deserializer=json.loads
    )
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine, autoflush=True, autocommit=True)

__all__ = [
    'Base',
    'Guild',
    'GuildPrefix',
    'User',
    'GuildUser',
    'Channel',
    'Message',
    'Command',
    'GuildCommand',
    "GuildRole",
    "GuildMemberActivity",
    "get_bases",
    "session"
]


def get_bases():
    return __all__
