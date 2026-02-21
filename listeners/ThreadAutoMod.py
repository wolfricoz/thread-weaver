import asyncio

import discord
from discord.ext.commands import Cog, Bot

from classes.discordcontrollers.forum.AutoMod import AutoMod


class ThreadAutoMod(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@Cog.listener('on_thread_create')
	async def on_thread_create(self, thread: discord.Thread) :
		"""This event is triggered when a thread is created."""
		message = await self.fetch_message(thread)
		if message is False:
			# the reason why we check none and false if because these have different meanings in this context.
			return
		if message is None :
			# TODO: add a log here for failed message fetches, this is important for debugging and improving the system.
			return
		await AutoMod().run(message)


	@Cog.listener('on_message_update')
	async def on_message_update(self, before, after) :
		"""This event is triggered when a message is updated."""
		pass

	@Cog.listener('on_message')
	async def on_message(self, message) :
		"""This event is triggered when a message is created."""
		pass


	async def fetch_message(self, thread: discord.Thread) -> discord.Message | None:
		"""Fetches the message that created the thread."""
		if thread.type != discord.ChannelType.public_thread:
			return False
		try :
			message = await thread.fetch_message(thread.id)
		except discord.NotFound :
			await asyncio.sleep(10)
			message = await thread.fetch_message(thread.id)
		return message




async def setup(bot: Bot) :
	await bot.add_cog(
		ThreadAutoMod(bot),
	)
