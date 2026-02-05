import logging
from collections.abc import AsyncIterator

import discordcontrollers
from discordcontrollers import Thread
from discordcontrollers.ext import commands

from classes.config import GuildConfig
from classes.support.queue import queue


class ForumTasks :

	def __init__(self, forum: discordcontrollers.ForumChannel, bot: commands.Bot) :
		# setting up the data all the underlying functions need to reduce api calls.
		self.forum: discordcontrollers.ForumChannel = forum
		self.threads: list[discordcontrollers.Thread] = forum.threads
		self.archived: AsyncIterator[Thread] = forum.archived_threads(limit=None)
		self.members: list[int] = [member.id for member in forum.guild.members]
		self.bot = bot

	async def start(self) :
		"""This starts the checking of the forum and will walk through all the tasks."""
		await self.recover_archived_posts()
		config = GuildConfig(self.forum.guild.id)
		if not config.get("cleanup"):
			return logging.info(f"Cleanup is disabled for {self.forum.guild.name}")
		for thread in self.threads :
			queue().add(self.cleanup_forum(thread), priority=0)

	async def recover_archived_posts(self) :
		"""Loop through archived posts and send a reminder there."""
		logging.info("recovering archived posts")
		async for archived_thread in self.archived :
			if archived_thread.archived is False :
				continue
			if len(self.forum.threads) >= 1000:
				logging.info(f"Too many threads in {self.forum.name}, skipping")
				return
			queue().add(archived_thread.edit(archived=False))

	async def cleanup_forum(self, thread: discordcontrollers.Thread) :
		logging.info("Cleaning up the forum")
		if self.check_user(thread.owner) is None :
			logging.info(f"{thread.name}'s user left, cleaning up")
			queue().add(thread.delete())
			return

	def check_user(self, member: discordcontrollers.Member) -> None | discordcontrollers.Member :
		if member is None :
			return None
		if member.id not in self.members :
			return None
		return member
