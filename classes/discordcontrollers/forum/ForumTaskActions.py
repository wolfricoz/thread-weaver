import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Any

import discord
import pytz
import re2
from discord import Thread
from discord.ext import commands
from discord_py_utilities.messages import send_message
from sqlalchemy import except_

from classes.kernel.ConfigData import ConfigData
from classes.kernel.queue import Queue
from classes.support.ThreadArchive import ThreadArchive
from data.enums.CleanUpTypes import CleanUpTypes
from resources.configs.ConfigMapping import ConfigMapping
from database.database import ForumCleanup, Forums

# This needs to be completely overhauled.

class ForumTask :

	def __init__(self, forum: discord.ForumChannel, config: Forums, bot: commands.Bot) :
		# setting up the data all the underlying functions need to reduce api calls.
		self.forum: discord.ForumChannel = forum
		self.config: Forums = config
		self.enabled_cleanups = [clean.key for clean in self.config.cleanup]
		self.threads: list[discord.Thread] = forum.threads
		self.archived: AsyncIterator[Thread] = forum.archived_threads(limit=None)
		self.members: list[int] = [member.id for member in forum.guild.members]
		self.bot = bot


	async def start(self) :
		"""This starts the checking of the forum and will walk through all the tasks."""
		await self.recover_archived_posts()

		if not ConfigData().get_toggle(self.forum.guild.id, ConfigMapping.CLEANUP_ENABLED, "ENABLED", "ENABLED") :
			logging.info(f"{self.forum.guild.name} does not have cleanup enabled, skipping.")
			return
		for thread in self.threads :
			# We loop through clean_up types, skipping those that aren't configured.
			Queue().add(self.cleanup_forum(thread), priority=0)


	async def recover_archived_posts(self) :
		"""Loop through archived posts and send a reminder there."""
		if not ConfigData().get_toggle(self.forum.guild.id, ConfigMapping.RESTORE_ARCHIVED, "ENABLED", "DISABLED"):
			return
		logging.info("recovering archived posts")
		active_threads: int = len(self.forum.guild.threads)

		async for archived_thread in self.archived :
			if not archived_thread.archived :
				continue
			if active_threads >= 950:
				logging.info(f"Too many threads in {self.forum.name}, skipping")
				return
			archived_thread += 1
			Queue().add(archived_thread.edit(archived=False))

	async def cleanup_forum(self, thread: discord.Thread) :
		delete = False
		reason = ""
		if not isinstance(thread, discord.Thread) :
			return

		if CleanUpTypes.ABANDONED in self.enabled_cleanups :
			delete, reason = self.check_user(thread.owner)
		if not delete and CleanUpTypes.OLD in self.enabled_cleanups :
			delete, reason = await self.check_age(thread)
		if not delete and CleanUpTypes.REGEX in self.enabled_cleanups :
			# this one just cleans up messages, it doesn't remove the thread.
			await self.check_regex(thread)
		if not delete and CleanUpTypes.MISSING in self.enabled_cleanups :
			delete, reason = await self.check_first_message(thread)
		await self.clean_up_thread(thread, delete, reason)




	# === Cleanup Checks ===


	def check_user(self, member: discord.Member) -> tuple[bool, str] :
		r = f""
		if member is None :
			return True, r
		if member.id not in self.members :
			return True, r
		return False, ""

	async def check_age(self, thread: discord.Thread):
		conf = self.fetch_cleanup_data(CleanUpTypes.OLD)
		if not conf.days:
			logging.warning(f"Failed to find days")
			return False, ""
		async for message in thread.history(limit=1, oldest_first=False):
			if message.created_at.astimezone(timezone.utc) < datetime.now(timezone.utc) - timedelta(days=conf.days):
				return True, f"`{thread.name}` has been automatically removed because it exceeded the {conf.days}-day age limit."


		return False, ""

	async def check_regex(self, thread):
		conf = self.fetch_cleanup_data(CleanUpTypes.REGEX)
		if not conf.extra:
			logging.warning(f"Failed to find regex")
			return False, ""

		try :
			options = re2.Options()
			options.case_sensitive = False
			regex = re2.compile(r"|".join([pattern.extra for pattern in conf]), options=options)
			message: discord.Message
			async for message in thread.history(limit=1000, oldest_first=False):

				result = regex.search(message.content)
				if result :
					Queue().add(message.delete(delay=5), 0)

		except re2.error as e :
			logging.warning(e, exc_info=True)
			return None, None
		return None, None


	async def check_first_message(self, thread: discord.Thread) -> tuple[bool, str] :
		try:
			message = await thread.fetch_message(thread.id)
		except discord.NotFound:
			return True, f"`{thread.name}` has been automatically removed because the main message was missing."
		except Exception as e:
			return False, ""
		return False, ""

	# === Support functions ===

	def fetch_cleanup_data(self, type: str) -> ForumCleanup | list[Any] | None :
		regex = []
		for c in self.config.cleanup:
			if c.key == type and type != CleanUpTypes.REGEX:
				return c
			if c.key == type and type == CleanUpTypes.REGEX:
				regex.append(c)
		if len(regex) >= 1 :
			return regex

		return None

	async def clean_up_thread(self, thread: discord.Thread, delete, reason):
		file_name = f"{thread.guild.name}_{thread.name}"
		if not delete:
			return
		channel = ConfigData().get_channel(thread.guild, ConfigMapping.CLEANUP_LOG, optional=True)
		if isinstance(channel, discord.TextChannel) :
			archiver = ThreadArchive(file_name, thread)
			await archiver.run()
			await send_message(channel, f"{thread.name} has been automatically removed: {reason}", files=[discord.File(fp=archiver.zip_path, filename=file_name)])
			await archiver.clean_up()
		Queue().add(thread.delete(reason=reason), 0)






