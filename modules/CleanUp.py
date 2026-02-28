import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.messages import send_message, send_response

from classes.discordcontrollers.forum.ForumController import ForumController
from classes.discordcontrollers.forum.ForumPatternController import ForumPatternController
from classes.kernel.AccessControl import AccessControl
from classes.kernel.ConfigData import ConfigData
from classes.support.regex import verify_regex_length, verify_regex_pattern
from data.enums.CleanUpTypes import CleanUpTypes
from database.transactions.ForumCleanupTransactions import ForumCleanupTransactions
from database.transactions.ForumTransactions import ForumTransactions
from resources.configs.ConfigMapping import ConfigMapping
from resources.configs.Limits import REGEX_MAX_LIMIT, REGEX_MIN_LIMIT

OPERATION_CHOICES = [
	Choice(name="Add", value="add"),
	Choice(name="Remove", value="remove"),
	Choice(name="List", value="list"),
]

class CleanUp(GroupCog, name="cleanup") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="abandoned",
	                      description=f"Toggle the removal of threads from users that left per forum. Disabled by default")
	@app_commands.checks.has_permissions(manage_channels=True)
	@app_commands.choices(operation=OPERATION_CHOICES)
	@AccessControl().check_premium()
	async def abandoned(self, interaction: discord.Interaction, operation: Choice['str']) :
		"""Toggle the removal of threads from users that left. Disabled by default

		Permissions:
		- Manage guild
		- Premium access
		"""
		if not ConfigData().get_toggle(interaction.guild.id, ConfigMapping.CLEANUP_ENABLED, "ENABLED", "ENABLED"):
			return await send_response(interaction, f"Your server does not have clean-up enabled! No changes have been made to the config.")

		_key = CleanUpTypes.ABANDONED
		if operation.value.lower() == "list" :
			forums = ForumTransactions().get_all(interaction.guild.id)
			formatted_message = "Forum's with abandoned post cleanup:\n"
			for forum in forums :
				result = ForumCleanupTransactions().get(forum.id, _key)
				if not result:
					continue
				formatted_message += f"- {forum.name}\n"

		forums = await ForumController.select_forums(interaction,
		                                  f"Please select the forum channel(s) where you want to {operation.value} cleanup of users that have left:")
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)

		# Process:
		# If the key exists, the forum is cleanup; if the key is removed then the forum is not clean-up.
		success = []
		_state = ""
		for forum in forums :
			match operation.value.lower() :
				case "add" :
					if not controller.check_forum_in_config(forum.id) :
						return await send_message(interaction.channel,
						                          f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
					ForumCleanupTransactions().add(forum.id, _key)
					success.append(forum)
					_state = "enabled"
				case "remove" :
					ForumCleanupTransactions().delete(forum.id, _key)
					success.append(forum)
					_state = "disabled"


		await send_response(interaction,
		                    f"Abandoned post cleanup is now {_state} in {', '.join([forum.name for forum in success])}",
		                    ephemeral=True)
		return None

	@app_commands.command(name="old",
	                      description=f"Toggle the removal of threads after a x amount of days per forum. Disabled by default")
	@app_commands.choices(operation=OPERATION_CHOICES)
	@app_commands.checks.has_permissions(manage_channels=True)
	@AccessControl().check_premium()
	async def old(self, interaction: discord.Interaction, operation: Choice['str'], days: int = 0) :
		"""Toggle the removal of threads after a x amount of days per forum. Disabled by default

		Permissions:
		- Manage guild
		- Premium access
		"""
		if not ConfigData().get_toggle(interaction.guild.id, ConfigMapping.CLEANUP_ENABLED, "ENABLED", "ENABLED"):
			return await send_response(interaction, f"Your server does not have clean-up enabled! No changes have been made to the config.")
		_key = CleanUpTypes.OLD
		forums = []
		if not operation.value.lower() == "list" :
			forums = await ForumController.select_forums(interaction,
			                                  f"Please select the forum channel(s) where you want to cleanup posts older than {days} days:")
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)

		# Process:
		# If the key exists, the forum is cleanup; if the key is removed then the forum is not clean-up.
		success = []

		match operation.value.lower() :
			case "add" :
				if days < 1 :
					return await send_response(interaction,
					                           "Please select a number of days to cleanup, you must choose more than 1 day.",
					                           ephemeral=True)
				for forum in forums :
					if not controller.check_forum_in_config(forum.id) :
						await send_message(interaction.channel,
						                   f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
						continue
					success.append(forum)
					ForumCleanupTransactions().add(forum.id, _key, days=days)

				await send_response(interaction,
				                    f"Posts older than {days} days in {', '.join([forum.mention for forum in success])} will be automatically removed.",
				                    ephemeral=True)

				return None
			case "remove" :
				for forum in forums :
					if not controller.check_forum_in_config(forum.id) :
						return await send_message(interaction.channel,
						                          f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
					success.append(forum)
					ForumCleanupTransactions().delete(forum.id, _key)

				await send_response(interaction,
				                    f"Removed the old post cleanup from {', '.join([forum.mention for forum in success])}.",
				                    ephemeral=True)
				return None
			case "list" :
				forums = ForumTransactions().get_all(interaction.guild.id)
				formatted_message = f"Forum's with old post cleanup:\n"
				for forum in forums :
					result = ForumCleanupTransactions().get(forum.id, _key)
					if not result :
						continue
					formatted_message += f"- {forum.name}: {result.days}\n"
				await send_response(interaction, formatted_message, ephemeral=True)
				return None
		return None

	@app_commands.command(name="regex",
	                      description=f"Toggle the removal of threads if regex is found (ADVANCED). Disabled by default")
	@app_commands.choices(operation=OPERATION_CHOICES)
	@app_commands.checks.has_permissions(manage_channels=True)
	@AccessControl().check_premium()
	async def regex(self, interaction: discord.Interaction, operation: Choice['str'], pattern:str, days: int = 0) :
		"""Toggle the removal of threads threads based on a regex, allowing for pings or other content to automatically be removed after x amount of days.

		Permissions:
		- Manage guild
		- Premium access
		"""
		if not ConfigData().get_toggle(interaction.guild.id, ConfigMapping.CLEANUP_ENABLED, "ENABLED", "ENABLED"):
			return await send_response(interaction, f"Your server does not have clean-up enabled! No changes have been made to the config.")
		_key = CleanUpTypes.REGEX
		forums = []
		if not operation.value.lower() == "list" :
			forums = await ForumController.select_forums(interaction,
			                                  f"Please select the forum channel(s) where you want to cleanup posts older than {days} days:")
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)

		# Process:
		# If the key exists, the forum is cleanup; if the key is removed then the forum is not clean-up.
		success = []

		match operation.value.lower() :
			case "add" :

				await send_response(interaction,
				                    f"Posts older than {days} days in {', '.join([forum.mention for forum in success])} will be automatically removed if they have regex: {pattern}.",
				                    ephemeral=True)

				valid_length = verify_regex_length(pattern)
				if not valid_length:
					await send_response(interaction, f"The provided pattern is too long ({REGEX_MAX_LIMIT}) or too short ({REGEX_MIN_LIMIT})", ephemeral=True)

				valid_pattern = verify_regex_pattern(pattern)
				if not valid_pattern:
					await send_response(interaction,
					                    "The provided pattern is not a valid regex pattern. Please check your pattern and try again.",
					                    ephemeral=True)

				if days < 1 :
					return await send_response(interaction,
					                           "Please select a number of days to cleanup, you must choose more than 1 day.",
					                           ephemeral=True)
				for forum in forums :
					if not controller.check_forum_in_config(forum.id) :
						await send_message(interaction.channel,
						                   f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
						continue
					success.append(forum)
					ForumCleanupTransactions().add(forum.id, _key, days=days, extra=valid_pattern)
					await send_response(interaction,
					                    f"Posts with {pattern} in {', '.join([forum.mention for forum in success])} will be automatically removed.",
					                    ephemeral=True)
				return None
			case "remove" :
				for forum in forums :
					if not controller.check_forum_in_config(forum.id) :
						return await send_message(interaction.channel,
						                          f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
					success.append(forum)
					ForumCleanupTransactions().delete(forum.id, _key)

				await send_response(interaction,
				                    f"Removed the regex cleanup from {', '.join([forum.mention for forum in success])}.",
				                    ephemeral=True)
				return None
			case "list" :
				forums = ForumTransactions().get_all(interaction.guild.id)
				formatted_message = f"Forum's with old post cleanup:\n"
				for forum in forums :
					result = ForumCleanupTransactions().get(forum.id, _key)
					if not result :
						continue
					formatted_message += f"- {forum.name}: {result.days}\n"
				await send_response(interaction, formatted_message, ephemeral=True)
				return None
		return None

	@app_commands.command(name="missing_starter",
	                      description=f"Toggle the removal of threads with a missing starter message. Disabled by default")
	@app_commands.checks.has_permissions(manage_channels=True)
	@app_commands.choices(operation=OPERATION_CHOICES)
	@AccessControl().check_premium()
	async def missing_starter(self, interaction: discord.Interaction, operation: Choice['str']) :
		"""Toggle the removal of threads with missing starter message. Disabled by default

		Permissions:
		- Manage guild
		- Premium access
		"""
		if not ConfigData().get_toggle(interaction.guild.id, ConfigMapping.CLEANUP_ENABLED, "ENABLED", "ENABLED") :
			return await send_response(interaction,
			                           f"Your server does not have clean-up enabled! No changes have been made to the config.")

		_key = CleanUpTypes.MISSING
		if operation.value.lower() == "list" :
			forums = ForumTransactions().get_all(interaction.guild.id)
			formatted_message = "Forum's with missing post cleanup:\n"
			for forum in forums :
				result = ForumCleanupTransactions().get(forum.id, _key)
				if not result :
					continue
				formatted_message += f"- {forum.name}\n"

		forums = await ForumController.select_forums(interaction,
		                                             f"Please select the forum channel(s) where you want to {operation.value} cleanup of posts that have a missing starter message:")
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)

		# Process:
		# If the key exists, the forum is cleanup; if the key is removed then the forum is not clean-up.
		success = []
		_state = ""
		for forum in forums :
			match operation.value.lower() :
				case "add" :
					if not controller.check_forum_in_config(forum.id) :
						return await send_message(interaction.channel,
						                          f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
					ForumCleanupTransactions().add(forum.id, _key)
					success.append(forum)
					_state = "enabled"
				case "remove" :
					ForumCleanupTransactions().delete(forum.id, _key)
					success.append(forum)
					_state = "disabled"

		await send_response(interaction,
		                    f"Abandoned post cleanup is now {_state} in {', '.join([forum.name for forum in success])}",
		                    ephemeral=True)
		return None





async def setup(bot: Bot) :
	await bot.add_cog(
		CleanUp(bot),
	)
