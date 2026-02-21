import logging
from enum import StrEnum
from typing import Literal

import discord
import re2
from discord import ForumChannel
from discord_py_utilities.messages import send_message

from classes.kernel.AccessControl import AccessControl
from classes.kernel.queue import Queue
from classes.support.singleton import Singleton
from data.enums.PatternTypes import ForumPatterns
from database.transactions.ForumTransactions import ForumTransactions
from views.v2.AutomodLayout import AutomodLayout


class AutoModActions(StrEnum) :
	BLOCK = "BLOCK"
	WARN = "WARN"
	ALLOW = "ALLOW"  # staff bypass
	REQUIRED = "REQUIRED"  # Same as block; but provides a different message to the user, telling them what they need to include in their message for it to be allowed, this makes it easier to differentiate the message.


class AutoMod(metaclass=Singleton) :
	_cache = {}

	messages = {

	}

	def __init__(self) :
		pass

	# == automod ==

	# future: Add a way for titles to be checked - not right now.

	async def run(self, message: discord.Message) :
		"""This function will run the auto moderation checks on the thread."""
		# check if we should activate the automoderation for this message, if not, return early to save resources.
		action: str | None = None
		reason = ""
		thread = message.channel
		forum = self.is_enabled(thread)
		if not forum :
			return

		# action = self.is_staff(message.author)
		logging.info(f"staff check disabled")
		# check simple blacklist first, as this is the least resource intensive check, and if it hits, we can skip the more resource intensive regex checks.
		if not action :
			action, reason = self.check_blacklist(message, forum)

		# Blocks defined pattern
		if not action and AccessControl().is_premium(forum.guild.id) :
			# logging.info(f"checking block patterns for {message.content}")
			action, reason = self.check_patterns(message.content, forum, ForumPatterns.block)
		# sends a warning when detected, but allows the message to go through.
		if not action and AccessControl().is_premium(forum.guild.id) :
			# logging.info(f"checking warn patterns for {message.content}")
			action, reason = self.check_patterns(message.content, forum, ForumPatterns.warn)
		# requires a pattern to be included in the message, if not, the message is blocked. Only checks the first message of the thread.
		if not action and AccessControl().is_premium(forum.guild.id) and message.id == thread.id:
			# logging.info(f"checking required patterns for {message.content}")
			action, reason = self.check_required_patterns(message.content, forum)
		# the final judgement
		logging.info(f"final action: {action}, reason: {reason}")
		await self.check_action(message, thread, forum, action, reason)

	def is_enabled(self, channel: discord.ForumChannel | discord.Thread) -> bool | ForumChannel :
		"""This checks if the automoderation is enabled for the forum."""
		if isinstance(channel, discord.Thread) :
			channel = channel.parent
		if not isinstance(channel, discord.ForumChannel) :
			return False
		if channel.id not in self.fetch_cache(channel.guild.id) :
			return False
		return channel

	def check_blacklist(self, message: discord.Message, forum: discord.ForumChannel) -> tuple[Literal[
		AutoModActions.BLOCK], str] | tuple[None, None] :
		"""This checks if the message contains any blacklisted words."""
		blacklisted_words = ForumTransactions().get_patterns_by_type(forum.id, ForumPatterns.blacklist)
		for word in blacklisted_words :
			if word.pattern.lower() in message.content.lower() :
				logging.info(f"blacklisted word {word.pattern.lower()}")
				return AutoModActions.BLOCK, f"Your message contains a blacklisted word: `{word.pattern}`"
		return None, None

	# TODO: Perhaps separate required patterns from this, it flexes the scope of this function a bit too much, and it would be cleaner to have a separate function for required patterns to provide a specific message with the regex; sending all the patterns would be too confusing.
	def check_patterns(self, content: list[str, str], forum: discord.ForumChannel,
	                   pattern_type: ForumPatterns | str) -> None | tuple[Literal[AutoModActions.BLOCK], str] | tuple[
		Literal[AutoModActions.WARN], str] | tuple[None, None] :
		"""This checks all the patterns for the forum and returns the action that should be taken."""
		try :
			patterns = ForumTransactions().get_patterns_by_type(forum.id, pattern_type)
			if not patterns or len(patterns) < 1:
				return None, None
			options = re2.Options()
			options.case_sensitive = False
			regex = re2.compile(r"|".join([pattern.pattern for pattern in patterns]), options=options)
			result = regex.search(content)
			if result :
				match pattern_type :
					case ForumPatterns.warn :
						return AutoModActions.WARN, f"This message triggered a content warning: `{result.group(0)}`, please check if the message breaks server policy."
					case _ :
						logging.info("blocking message")
						return AutoModActions.BLOCK, f"Your message contains content that is not allowed: `{result.group(0)}` "

		except re2.error as e :
			logging.warning(e, exc_info=True)
			return None, None
		return None, None

	def check_required_patterns(self, content: str, forum: discord.ForumChannel) -> tuple[Literal[
		AutoModActions.REQUIRED], str] | tuple[None, None] :
		"""This checks all the required patterns for the forum and returns whether the message should be blocked or not, along with a message to the user about what they need to include in their message."""

		pattern_type = ForumPatterns.required
		patterns = ForumTransactions().get_patterns_by_type(forum.id, pattern_type)
		options = re2.Options()
		options.case_sensitive = False
		for pattern in patterns :

			regex = re2.compile(rf"{pattern.pattern}", options=options)
			result = regex.search(content)
			if result :
				continue
			return AutoModActions.REQUIRED, f"Your message is missing required content: `{regex.pattern}`"
		return None, None

	async def check_action(self, message, thread, forum, action, reason="") :
		"""This checks the action that should be taken for the message."""

		match action :
			case AutoModActions.BLOCK :
				embed = AutomodLayout(
					rule_type="Forbidden Content",
					reason=reason,
					title=thread.name,
					content=message.content,
				)
				Queue().add(send_message(message.author, f" ", view=embed))
				if message.id == thread.id :

					await thread.delete()
				else :
					await message.delete()
				return None
			case AutoModActions.WARN :
				embed = AutomodLayout(
					rule_type="Content Warning",
					reason=reason,
					title=thread.name,
					content=message.content,
				)
				# Queue().add(send_message(message.author, f" ", view=embed))

				return None
			case AutoModActions.ALLOW :
				return None

			case AutoModActions.REQUIRED:
					embed = AutomodLayout(
						rule_type="Missing Required Content",
						reason=reason,
						title=thread.name,
						content=message.content,
					)
					Queue().add(send_message(message.author, f" ", view=embed))
					if message.id == thread.id :
						await thread.delete()
					else :
						await message.delete()
					return None
			case _ :
				return None


	def is_staff(self, member: discord.Member) -> str | None :
		"""This checks if the member is a staff member."""
		if member.guild_permissions.administrator or member.guild_permissions.manage_messages or member.guild_permissions.manage_guild or member.guild_permissions.manage_channels :
			return AutoModActions.ALLOW
		return None


	# == Cache functions ==

	def fetch_cache(self, guild_id: int) -> list[dict] :
		"""Fetches the cache for the guild, if it doesn't exist, it creates an empty cache."""

		if guild_id not in self._cache :
			forums = ForumTransactions().get_all(guild_id, id_only=True)
			self._cache[guild_id] = list(forums)
		return self._cache[guild_id]


	def clear_cache(self) :
		"""Clears the cache."""
		self._cache = {}
