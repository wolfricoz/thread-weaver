import discord
from discord import Message
from discord_py_utilities.messages import send_message

from classes.kernel.AccessControl import AccessControl
from database.transactions.ForumTransactions import ForumTransactions
from resources.configs.FreeLimits import FREE_BLACKLIST_WORD_LIMIT


class ForumPatternController :

	def __init__(self, guild_id: int) :
		self.forums = [forum.id for forum in ForumTransactions().get_all(guild_id)]
		pass

	def check_forum_in_config(self, channel_id: int) :
		if channel_id not in self.forums :
			return False
		return True

	async def add_pattern(self, interaction: discord.Interaction, channel: discord.TextChannel | discord.ForumChannel,
	                      name: str, pattern: str, action: str = "BLOCK") -> Message | None :
		if not self.check_forum_in_config(channel.id) :
			return await send_message(interaction.channel,
			                          f"{channel.name} is not registered as a forum channel. Please add it first using `/forum add`.")

		pattern_count = ForumTransactions().count_patterns(channel.id)
		if pattern_count >= FREE_BLACKLIST_WORD_LIMIT and not AccessControl().is_premium(interaction.guild.id) :
			return await send_message(interaction.channel,
			                          f"You have reached the limit of {FREE_BLACKLIST_WORD_LIMIT} blacklisted words for {channel.name}. Please remove some words or upgrade to premium to add more.",
			                          )
		ForumTransactions().add_pattern(
			channel_id=channel.id,
			name=name.lower(),
			action=action.upper(),
			pattern=pattern.lower(),
		)

		return None

	async def remove_pattern(self, interaction: discord.Interaction, channel: discord.TextChannel | discord.ForumChannel,
	                         name: str) -> Message | None :
		if not self.check_forum_in_config(channel.id) :
			return await send_message(interaction.channel,
			                          f"{channel.name} is not registered as a forum channel. Please add it first using `/forum add`.")

		pattern = ForumTransactions().get_pattern(channel.id, name.lower())
		if pattern is None :
			return await send_message(interaction.channel, f"No pattern with the name `{name}` found for {channel.name}.")
		ForumTransactions().remove_pattern(pattern.id)
		return None
