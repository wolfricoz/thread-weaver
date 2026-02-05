import logging
import re

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import Bot, GroupCog
from discord_py_utilities.messages import send_message, send_response

from classes.Blacklist import Blacklist
from classes.forumtasks import ForumTasks
from classes.kernel.AccessControl import AccessControl
from classes.kernel.queue import Queue
from database.transactions.ForumTransactions import ForumTransactions
from resources.configs.FreeLimits import FREE_BLACKLIST_WORD_LIMIT
from views.select.ForumSelect import ForumSelect


class Forums(GroupCog, name="forum", description="Forum management commands") :
	"""
	Forum management commands

	"""

	def __init__(self, bot: Bot) :
		self.bot = bot

	async def select_forums(self, interaction: discord.Interaction, response: str) :
		forumselect = ForumSelect()
		await send_response(interaction, response, view=forumselect, ephemeral=True)
		await forumselect.wait()
		return forumselect.selected_channels

	@app_commands.command(name="add", description="Adds the forums to the bots database")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def add(self, interaction: discord.Interaction) :
		"""
		Adds the chosen forum channel for the bot, enabling the features the bot provides for forum channels.

		Permissions:
		- Manage guild
		"""
		forums = self.select_forums(interaction, "Select your forum channel(s) to add")
		for forum in forums :
			ForumTransactions().add(
				channel_id=forum.id,
				server_id=interaction.guild.id,
				name=forum.name,
			)
		await interaction.followup.send(f"Added {len(forums)} forum channel(s) to the database.", ephemeral=True)

	@app_commands.command(name="remove", description="Removes the chosen forum channel for the bot")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def remove(self, interaction: discord.Interaction) :
		"""
		Removes the chosen forum channel from the bot's database, disabling the features the bot provides for forum channels.

		Permissions:
		- Manage guild
		"""

		forums = await self.select_forums(interaction, "Select your forum channel(s) to remove")
		for forum in forums :
			ForumTransactions().delete(forum.id)
		await send_response(interaction, f"Removed {len(forums)} forum channel(s) from the database.", ephemeral=True)

	@app_commands.command(name="add_pattern", description="Adds a pattern for forum threads to check (regex)")
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.choices(
		action=[
			Choice(name="Delete Thread", value="block"),
			Choice(name="Warn staff", value="warn"),
		]
	)
	@AccessControl().check_premium()
	async def add_pattern(self, interaction: discord.Interaction, name: str, pattern: str, action: Choice[str]) :
		"""
		Adds a pattern for forum threads to check.

		[Include a guide here on regex patterns and how to use them]

		Permissions:
		- Manage guild
		"""
		try :
			re.compile(pattern)
		except re.error :
			await send_response(interaction,
			                    f"The provided pattern is not a valid regex pattern. Please check your pattern and try again.",
			                    ephemeral=True)
			return

		forums = self.select_forums(interaction,
		                            "Select your forum channel(s) to add the pattern to! Patterns are [Regex-based](https://regex101.com/), so make sure to test them there first.")
		for forum in forums :
			ForumTransactions().add_pattern(
				channel_id=forum.id,
				name=name,
				action=action.value.upper(),
				pattern=pattern,
			)

		await send_response(interaction, f"Added pattern to {len(forums)} forum channel(s).", ephemeral=True)

	@app_commands.command(name="blacklist_word", description="Adds/Removes a word to the forum blacklist [simple]")
	@app_commands.choices(operation=[
		Choice(name="Add", value="add"),
		Choice(name="Remove", value="remove"),
		Choice(name="List", value="list"),
	])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def blacklist_word(self, interaction: discord.Interaction, operation: Choice[str], word: str) :
		"""
		Adds/Removes a word to the forum blacklist [simple]

		Permissions:
		- Manage guild
		"""
		forums = self.select_forums(interaction,
		                            f"Select your forum channel(s) to {operation.value} the word `{word}` to the blacklist!")
		for forum in forums :
			match operation.value.lower() :

				case "add" :
					await Blacklist.add_pattern(interaction, forum, word, word, action="BLACKLIST")

				case "remove" :
					await Blacklist.remove_pattern(interaction, forum, word)
				case "list":
					words = ForumTransactions().get_all_patterns(forum.id)
					await send_response(interaction, f"Blacklisted words for {forum.name}:\n" + "\n".join([f"{pattern.name}: `{pattern.pattern}` (Action: {pattern.action})" for pattern in words]), ephemeral=True)


		await send_response(interaction,
		                    f"{operation.name}ed the word `{word}` {'to' if operation.value == 'add' else 'from'} the blacklist for {len(forums)} forum channel(s).",
		                    ephemeral=True)


	@app_commands.command(name='stats')
	@app_commands.checks.has_permissions(manage_channels=True)
	async def stats(self, interaction: discord.Interaction, forum: discord.ForumChannel) :
		"""Get stats for a forum"""
		await send_response(interaction, f"Getting stats for {forum.name}", ephemeral=True)
		embed = discord.Embed(title=f"Stats for {forum.name}")
		data = {
			"Threads"      : len(forum.threads),
			"archived"     : len([thread for thread in forum.threads if thread.archived]),
			"tags"         : ", ".join([tag.name for tag in forum.available_tags]),
			"layout"       : forum.default_layout,
			"sort mode"    : forum.default_sort_order,
			"slowmode"     : forum.default_thread_slowmode_delay,
			"auto archive" : forum.default_auto_archive_duration,
			"reaction"     : forum.default_reaction_emoji
		}
		for key, value in data.items() :
			embed.add_field(name=key, value=value, inline=False)
		await send_message(interaction.channel, embed=embed)


	@app_commands.command(name="recover", description="Recover archived posts")
	@app_commands.checks.has_permissions(manage_channels=True)
	async def recover(self, interaction: discord.Interaction, forum: discord.ForumChannel) :
		"""Recover archived posts"""
		await send_response(interaction, f"Recovering archived posts for {forum.name}, this may take some time.",
		                    ephemeral=True)
		archived_thread: discord.Thread
		channel: discord.ForumChannel
		regex = re.compile(f"search", flags=re.IGNORECASE)
		channels = [
			channel
			for channel in interaction.guild.channels
			if channel.type == discord.ChannelType.forum and regex.search(channel.name)
		]
		for channel in channels :
			logging.debug(f"[Forum Manager] Checking {channel.name}")
			forum = ForumTasks(channel, self.bot)
			Queue().add(forum.start())


	@app_commands.command(name="copy", description="Copy a forum with all settings!")
	@app_commands.checks.has_permissions(manage_channels=True)
	async def copy(self, interaction: discord.Interaction, forum: discord.ForumChannel, name: str = None) :
		"""Copy a forum with all settings!"""
		await send_response(interaction, "Copying a forum with all settings!", ephemeral=True)
		f = await forum.clone(name=f"{name if name else forum.name}-Copy", category=forum.category)
		[await f.create_tag(name=tag.name, moderated=tag.moderated, emoji=tag.emoji,
		                    reason="Forum copied through forum manager") for tag in forum.available_tags if
		 tag.name not in f.available_tags]
		Queue().add(f.edit(default_thread_slowmode_delay=forum.default_thread_slowmode_delay,
		                   default_auto_archive_duration=forum.default_auto_archive_duration,
		                   default_layout=forum.default_layout,
		                   default_sort_order=forum.default_sort_order,
		                   default_reaction_emoji=forum.default_reaction_emoji), priority=2)
		await send_message(interaction.channel, f"Forum {forum.mention} copied to {f.mention}")


# @app_commands.command(name="cleanup_toggle")
# async def cleanup_toggle(self, interaction: discord.Interaction, active: bool) :
# 	"""Toggle the removal of threads from users that left. Disabled by default"""
# 	config = GuildConfig(interaction.guild.id)
# 	config.set("cleanup", active)
# 	await send_response(interaction, f"Cleanup is now {active}", ephemeral=True)

@app_commands.command(name="purge")
async def purge(self, interaction: discord.Interaction, forum: discord.ForumChannel, notify_user: bool = False) :
	"""Purge all threads in a forum, notify_user returns the contents of the thread to the user that started it."""
	await send_response(interaction, f"Purge all threads in {forum.name}", ephemeral=True)
	for thread in forum.threads :
		if notify_user :
			try :
				starter_msg = await thread.fetch_message(thread.id)
			except discord.NotFound :
				logging.error(
					f"Could not fetch message for thread {thread.name} in {forum.name}, it might have been deleted.")
				starter_msg = None
			if not starter_msg :
				logging.error(f"Could not fetch message for thread {thread.name} in {forum.name}")
				Queue().add(thread.delete())
				continue
			Queue().add(send_message(thread.owner,
			                         f"Your thread {thread.name} in {forum.name} is being purged, here are the contents:"
			                         f"\ntitle: {thread.name}\ncontent: {starter_msg.content}"), priority=2)
		Queue().add(thread.delete())
	else :
		Queue().add(send_message(interaction.channel, f"Purge complete for {forum.name}"), 0)
	Queue().add(send_message(interaction.channel, f"Queueing purge of {len(forum.threads)} threads in {forum.name}."),
	            priority=2)


async def setup(bot: Bot) :
	await bot.add_cog(
		Forums(bot),
	)
