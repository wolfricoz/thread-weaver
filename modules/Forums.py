import logging
import re

import discord
from classes.forumtasks import ForumTasks
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import Bot, GroupCog
from discord_py_utilities.messages import send_message, send_response

from classes.discordcontrollers.forum.ForumController import ForumController
from classes.discordcontrollers.forum.ForumPatternController import ForumPatternController
from classes.kernel.AccessControl import AccessControl
from classes.kernel.queue import Queue
from classes.support.regex import verify_regex, verify_regex_length, verify_regex_pattern
from database.transactions.ForumTransactions import ForumTransactions
from resources.configs.Limits import REGEX_MAX_LIMIT, REGEX_MIN_LIMIT

OPERATION_CHOICES = [
	Choice(name="Add", value="add"),
	Choice(name="Remove", value="remove"),
	Choice(name="List", value="list"),
]


class Forums(GroupCog, name="forum", description="Forum management commands") :
	"""
	Forum management commands

	"""

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="add", description="Adds the forums to the bots database")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def add(self, interaction: discord.Interaction) :
		"""
		Adds the chosen forum channel for the bot, enabling the features the bot provides for forum channels.

		Permissions:
		- Manage guild
		"""
		forums = ForumController.select_forums(interaction, "Select your forum channel(s) to add")
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

		forums = await ForumController.select_forums(interaction, "Select your forum channel(s) to remove")
		for forum in forums :
			ForumTransactions().delete(forum.id)
		await send_response(interaction, f"Removed {len(forums)} forum channel(s) from the database.", ephemeral=True)

	@app_commands.command(name="patterns", description="Adds/removes/lists patterns for forum threads (regex)")
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.choices(
		operation=OPERATION_CHOICES,
		action=[
			Choice(name="Delete Thread", value="block"),
			Choice(name="Warn staff", value="warn"),
		],
	)
	@AccessControl().check_premium()
	async def add_pattern(self, interaction: discord.Interaction, operation: Choice[str], name: str = None,
	                      pattern: str = None, action: Choice[str] = None) :
		"""
		Add / Remove / List patterns for forum threads.

		Permissions:
		- Manage guild
		"""
		success = 0
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)
		forums = await ForumController.select_forums(interaction,
		                                             "Please select the forum channel(s) you want to manage patterns for:")
		match operation.value.lower() :
			case "add" :
				if not name or not pattern or not action :
					await send_response(interaction,
					                    "To add a pattern you must provide `name`, `pattern` and `action`.",
					                    ephemeral=True)
					return

				valid_length = verify_regex_length(pattern)
				if not valid_length:
					await send_response(interaction, f"The provided pattern is too long ({REGEX_MAX_LIMIT}) or too short ({REGEX_MIN_LIMIT})", ephemeral=True)

				valid_pattern = verify_regex_pattern(pattern)
				if not valid_pattern:
					await send_response(interaction,
					                    "The provided pattern is not a valid regex pattern. Please check your pattern and try again.",
					                    ephemeral=True)
				logging.info(valid_pattern)

				for forum in forums :
					result = await controller.add_pattern(interaction, forum, name, pattern, action.value.upper())
					if result is not None :
						return
					success += 1

				await send_response(interaction, f"Added pattern to {success} forum channel(s).", ephemeral=True)

			case "remove" :
				if not name :
					await send_response(interaction,
					                    "To remove a pattern you must provide the `pattern` to remove.",
					                    ephemeral=True)

					return

				for forum in forums :
					# Expecting a removal method on ForumTransactions; adjust if your API differs.
					result = await controller.remove_pattern(interaction, forum, name)
					if result is not None :
						return
					success += 1

				await send_response(interaction, f"Removed pattern from {success} forum channel(s).", ephemeral=True)

			case "list" :
				for forum in forums :
					patterns = ForumTransactions().get_all_patterns(forum.id)
					if not patterns :
						await send_response(interaction, f"No patterns configured for {forum.name}.", ephemeral=True)
						continue
					formatted = "\n".join([f"{p.name}: `{p.pattern}` (Action: {p.action})" for p in patterns])
					await send_response(interaction, f"Patterns for {forum.name}:\n{formatted}", ephemeral=True)
				return

	@app_commands.command(name="blacklist_word", description="Adds/Removes a word to the forum blacklist [simple]")
	@app_commands.choices(operation=[

	])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def blacklist_word(self, interaction: discord.Interaction, operation: Choice[str], word: str) :
		"""
		Adds/Removes a word to the forum blacklist [simple]

		Permissions:
		- Manage guild
		"""
		forums = await ForumController.select_forums(interaction,
		                                             f"Select your forum channel(s) to {operation.value} the word `{word}` to the blacklist!")
		blacklist = ForumPatternController(interaction.guild.id)
		success = 0
		for forum in forums :
			match operation.value.lower() :

				case "add" :
					result = await blacklist.add_pattern(interaction, forum, word, word, action="BLACKLIST")
					if result is not None :
						return
					success += 1

				case "remove" :
					result = await blacklist.remove_pattern(interaction, forum, word)
					if result is not None :
						return
					success += 1
				case "list" :
					words = ForumTransactions().get_all_patterns(forum.id)
					await send_response(interaction, f"Blacklisted words for {forum.name}:\n" + "\n".join(
						[f"{pattern.name}: `{pattern.pattern}` (Action: {pattern.action})" for pattern in words]), ephemeral=True)

		if operation.value.lower() == "list" :
			return
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

	@app_commands.command(name="add_all", description="Adds all forums to the bot.")
	@app_commands.checks.has_permissions(manage_channels=True)
	async def add_all(self, interaction: discord.Interaction) :
		forums = [forum for forum in interaction.guild.channels if forum.type == discord.ChannelType.forum]
		for forum in forums :
			ForumTransactions().add(forum.id, interaction.user.id, forum.name)
		await send_response(interaction, f"Successfully added all forums to {interaction.user.name}!")

	# Config here:
	# - Prevent duplicates (Local, global, off)
	# - Thread log

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
