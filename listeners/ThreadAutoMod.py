import asyncio

import discord
from discord.ext.commands import Cog, Bot
from discord_py_utilities.messages import send_message

from classes.discordcontrollers.forum.AutoMod import AutoMod
from classes.kernel.ConfigData import ConfigData
from resources.configs.ConfigMapping import ConfigMapping


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
		if ConfigData().get_toggle(thread.guild.id, ConfigMapping.PING_ON_THREAD, "ENABLED", "DISABLED") :
			channel = await ConfigData().get_channel(thread.guild, ConfigMapping.PING_ON_THREAD_CHANNEL)
			ping = ConfigData().get_key(thread.guild.id, ConfigMapping.PING_ON_THREAD_ROLE, 0)
			payload = f"<@{ping}>\n`{thread.name}` created by {thread.owner.mention} in {thread.parent.name}"
			if ping == 0:
				payload = f"`{thread.name}` created by {thread.owner.mention} in {thread.parent.name}"
			await send_message(channel, payload)

		await AutoMod().run(message)


	@Cog.listener('on_message_edit')
	async def on_message_edit(self, before, after) :
		"""This event is triggered when a message is updated."""
		await AutoMod().run(after)


	@Cog.listener('on_message')
	async def on_message(self, message) :
		"""This event is triggered when a message is created."""
		if message.id == message.channel.id:
			return
		await AutoMod().run(message)



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
