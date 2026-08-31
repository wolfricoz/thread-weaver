"""Slash-command channel options that survive a cache miss.

discord.py resolves a channel option purely from the bot's cache: ``Guild.get_channel`` for
guild channels, ``Guild.get_thread`` for threads. The thread cache only holds *active* threads —
the gateway evicts a thread the moment it is archived — so picking an archived forum post makes
the built-in transformer raise ``TransformerError`` before the command body ever runs. For a
forum bot that archives threads itself, that is the common case, not the edge case.

The transformers here fall back to an API fetch when the cache misses, so archived and merely
uncached channels behave like any other. Only a real access problem fails now, and it fails as a
``ChannelAccessError`` carrying a message the user can act on.

Usage:

	async def export(self, interaction: discord.Interaction, thread: ThreadOption) : ...

``ThreadOption`` still type-hints as ``discord.Thread``, so nothing downstream changes.
"""
import logging

import discord
from discord import app_commands

# Which Discord channel types Discord should offer in the picker for a given python type.
# Extend this when a command needs an option type that isn't listed yet.
CHANNEL_TYPES: dict[type, list[discord.ChannelType]] = {
	discord.Thread      : [discord.ChannelType.public_thread, discord.ChannelType.private_thread,
	                       discord.ChannelType.news_thread],
	discord.ForumChannel: [discord.ChannelType.forum, discord.ChannelType.media],
	discord.TextChannel : [discord.ChannelType.text, discord.ChannelType.news],
}


class ChannelAccessError(app_commands.AppCommandError) :
	"""A channel option could not be used, for a reason worth showing the user.

	The message is written for the person who ran the command, so the error handler can print
	``str(error)`` directly instead of guessing at a cause.
	"""


class CachelessChannelTransformer(app_commands.Transformer) :
	"""Resolves a channel option from cache, then from the API if the cache misses."""

	def __init__(self, *channel_types: type) :
		super().__init__()
		unknown = [t for t in channel_types if t not in CHANNEL_TYPES]
		if unknown :
			raise TypeError(f"No channel type mapping for {unknown}, add it to CHANNEL_TYPES.")
		self._types: tuple[type, ...] = channel_types
		self._allowed: list[discord.ChannelType] = [
			channel_type for t in channel_types for channel_type in CHANNEL_TYPES[t]
		]
		self._display_name = " or ".join(t.__name__.replace("Channel", "").lower() for t in channel_types)

	@property
	def type(self) -> discord.AppCommandOptionType :
		return discord.AppCommandOptionType.channel

	@property
	def channel_types(self) -> list[discord.ChannelType] :
		return self._allowed

	@property
	def _error_display_name(self) -> str :
		return self._display_name

	async def transform(self, interaction: discord.Interaction, value) :
		# Already a full object (raw channel types are handed over as-is).
		if isinstance(value, self._types) :
			return value

		# Cache hit: an active thread, or a guild channel the bot can see.
		resolved = value.resolve()
		if isinstance(resolved, self._types) :
			return resolved

		# Cache miss. Archived thread, a channel we haven't seen this session, or no access.
		return await self.fetch(interaction, value)

	async def fetch(self, interaction: discord.Interaction, value) :
		"""Fetch the channel from the API and turn any failure into a readable error."""
		name = discord.utils.escape_markdown(str(getattr(value, "name", value)))
		channel_id = getattr(value, "id", None)
		if channel_id is None :
			raise ChannelAccessError(f"Could not read `{name}` as a {self._display_name}. "
			                         f"Please pick it from the list Discord suggests.")

		try :
			fetched = await interaction.client.fetch_channel(channel_id)
		except discord.Forbidden :
			raise ChannelAccessError(
				f"I can't access `{name}`. Forum Manager is missing the **View Channel** permission "
				f"there (or in its parent channel). Grant it access and run the command again.") from None
		except discord.NotFound :
			raise ChannelAccessError(f"`{name}` no longer exists — it was probably deleted.") from None
		except discord.HTTPException as e :
			logging.warning(f"[Forum Manager] Failed to fetch channel {channel_id} for a command option: {e}")
			raise ChannelAccessError(f"Discord did not return `{name}`. Please try again in a moment.") from None

		if not isinstance(fetched, self._types) :
			raise ChannelAccessError(f"`{name}` is not a {self._display_name}.")
		return fetched


ThreadOption = app_commands.Transform[discord.Thread, CachelessChannelTransformer(discord.Thread)]
ForumOption = app_commands.Transform[discord.ForumChannel, CachelessChannelTransformer(discord.ForumChannel)]
TextChannelOption = app_commands.Transform[discord.TextChannel, CachelessChannelTransformer(discord.TextChannel)]
