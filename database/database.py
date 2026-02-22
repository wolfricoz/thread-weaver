# python
import os
from datetime import datetime
from typing import List

import pymysql
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func
from sqlalchemy_utils import create_database, database_exists

from data.env.loader import env, load_environment

load_environment()

pymysql.install_as_MySQLdb()

engine = create_engine(
	f"{env('DB_TYPE', 'mysql')}://{env('DB_USER', 'username')}:{env('DB_PASSWORD', 'password')}@{env('DB_HOST', '127.0.0.1')}:{env('DB_PORT', '3306')}/{env('DB_NAME', 'template')}",
	poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
if not database_exists(engine.url) :
	create_database(engine.url)

conn = engine.connect()


class Base(DeclarativeBase) :
	pass


class Config(Base) :
	__tablename__ = "config"
	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	guild: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.id", ondelete="CASCADE"))
	key: Mapped[str] = mapped_column(String(512))
	value: Mapped[str] = mapped_column(String(1980))


class Servers(Base) :
	__tablename__ = "servers"
	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
	owner: Mapped[str] = mapped_column(String(1024))
	name: Mapped[str] = mapped_column(String(1024))
	member_count: Mapped[int] = mapped_column(BigInteger)
	hidden: Mapped[bool] = mapped_column(Boolean, default=False)
	invite: Mapped[str] = mapped_column(String(256), default="")
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
	deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=None, nullable=True)
	active: Mapped[bool] = mapped_column(Boolean, default=True)
	premium: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
	owner_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
	forums: Mapped[List["Forums"]] = relationship("Forums", back_populates="server", cascade="all, delete-orphan")

	def __int__(self) :
		return self.id


class Forums(Base) :
	__tablename__ = "forums"
	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
	server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.id", ondelete="CASCADE"))
	name: Mapped[str] = mapped_column(String(1024))
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	server: Mapped["Servers"] = relationship("Servers", back_populates="forums")
	minimum_characters: Mapped[int] = mapped_column(BigInteger, default=0)
	duplicates: Mapped[bool] = mapped_column(Boolean, default=True)
	patterns: Mapped[List["ForumPatterns"]] = relationship("ForumPatterns", back_populates="forum",
	                                                       cascade="all, delete-orphan")
	cleanup: Mapped[List["ForumPatterns"]] = relationship("ForumCleanup", back_populates="forum",
	                                                       cascade="all, delete-orphan")


class ForumPatterns(Base) :
	__tablename__ = "forum_patterns"
	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(256))
	forum_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("forums.id", ondelete="CASCADE"))
	action: Mapped[str] = mapped_column(String(100))
	pattern: Mapped[str] = mapped_column(String(1000))
	forum: Mapped["Forums"] = relationship("Forums", back_populates="patterns")


class ForumCleanup(Base) :
	__tablename__ = "forum_cleanup"
	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
	forum_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("forums.id", ondelete="CASCADE"), unique=True)
	key: Mapped[str] = mapped_column(String(100)) # CLEANUPLEFT, CLEANUPDAYS
	days: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)
	extra: Mapped[str] = mapped_column(Text, nullable=True)
	forum: Mapped["Forums"] = relationship("Forums", back_populates="cleanup")


class Staff(Base) :
	__tablename__ = "staff"
	id: Mapped[int] = mapped_column(primary_key=True)
	uid: Mapped[int] = mapped_column(BigInteger)
	role: Mapped[str] = mapped_column(String(128))

	def __int__(self) :
		return self.id


class database :
	@staticmethod
	def create() :
		Base.metadata.create_all(engine)
		print("Database built")


def create_bot_database() :
	Base.metadata.create_all(engine)


def drop_bot_database() :
	if os.getenv('DISCORD_TOKEN') is not None :
		raise Exception("You cannot drop the database while the bot is in production")
	Session = sessionmaker(bind=engine)
	session = Session()
	session.close_all()
	Base.metadata.drop_all(engine)
