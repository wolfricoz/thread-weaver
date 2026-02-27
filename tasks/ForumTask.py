import logging

from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from classes.discordcontrollers.forum.AutoMod import AutoMod


class ForumTask(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		# register tasks
		self.check_forums_task.start()

	def cog_unload(self) -> None:
		# unregister tasks
		self.check_forums_task.cancel()

	pass

	# this task will run every 30 minutes, you can change the time interval as needed!
	@tasks.loop(hours=1)
	async def check_forums_task(self) :
		# This is a sample task that runs every 30 minutes.
		logging.info("Sample task is running...")
		# You can add your periodic task logic here.
		# - For example, checking for updates, sending reminders, etc.

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
