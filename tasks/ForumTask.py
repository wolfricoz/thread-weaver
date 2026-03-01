import logging

import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from classes.discordcontrollers.forum.AutoMod import AutoMod
from classes.discordcontrollers.forum.ForumTaskActions import ForumTask as ForumManager
from classes.kernel.queue import Queue
from database.transactions.ForumTransactions import ForumTransactions


class ForumTask(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		# register tasks
		self.check_forums_task.start()

	def cog_unload(self) -> None:
		# unregister tasks
		self.check_forums_task.cancel()

	pass

	@tasks.loop(hours=24)
	async def check_forums_task(self) :
		# This is a sample task that runs every 30 minutes.
		logging.info("Checking forums...")
		for guild in  self.bot.guilds:
			forum_configs = ForumTransactions().get_all(guild.id)
			for forum_config in forum_configs :
				f = guild.get_channel(forum_config.id)
				if f is None or not isinstance(f, discord.ForumChannel):
					continue
				forum_manager = ForumManager(f, forum_config, self.bot)
				Queue().add(forum_manager.start(), 0)

	@tasks.loop(hours=1)
	async def clear_cache(self):
		logging.info("Clearing automod cache...")
		AutoMod().clear_cache()


	@check_forums_task.before_loop
	async def before_check_task(self) :
		# Wait until the bot is ready before starting the task
		await self.bot.wait_until_ready()



async def setup(bot: Bot) :
	await bot.add_cog(
		ForumTask(bot),
	)
