import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.messages import send_message, send_response

from classes.discordcontrollers.forum.ForumController import ForumController
from classes.discordcontrollers.forum.ForumPatternController import ForumPatternController
from classes.kernel.AccessControl import AccessControl
from database.transactions.ForumCleanupTransactions import ForumCleanupTransactions
from database.transactions.ForumTransactions import ForumTransactions

OPERATION_CHOICES = [
	Choice(name="Add", value="add"),
	Choice(name="Remove", value="remove"),
	Choice(name="List", value="list"),
]

class CleanUp(GroupCog, name="cleanup") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="cleanup_left",
	                      description=f"Toggle the removal of threads from users that left per forum. Disabled by default")
	@app_commands.checks.has_permissions(manage_channels=True)
	@AccessControl().check_premium()
	async def cleanup_left(self, interaction: discord.Interaction, active: bool) :
		"""Toggle the removal of threads from users that left. Disabled by default"""
		_key = "CLEANUPLEFT"
		forums = await ForumController.select_forums(interaction,
		                                  f"Please select the forum channel(s) where you want to {'enable' if active else 'disable'} cleanup of users that have left:")
		controller: ForumPatternController = ForumPatternController(interaction.guild.id)

		# Process:
		# If the key exists, the forum is cleanup; if the key is removed then the forum is not clean-up.
		success = []
		for forum in forums :
			if not controller.check_forum_in_config(forum.id) :
				return await send_message(interaction.channel,
				                          f"{forum.name} is not registered as a forum channel. Please add it first using `/forum add`.")
			success.append(forum)
			if active :
				ForumCleanupTransactions().add(forum.id, _key)
				continue
			ForumCleanupTransactions().delete(forum.id, _key)

		await send_response(interaction,
		                    f"Abandoned post cleanup is now {'enabled' if active else 'disabled'} in {', '.join([forum.name for forum in success])}",
		                    ephemeral=True)
		return None

	@app_commands.command(name="cleanup_old",
	                      description=f"Toggle the removal of threads after a x amount of days per forum. Disabled by default")
	@app_commands.choices(operation=OPERATION_CHOICES)
	@app_commands.checks.has_permissions(manage_channels=True)
	@AccessControl().check_premium()
	async def cleanup_toggle(self, interaction: discord.Interaction, operation: Choice['str'], days: int = 0) :
		"""Toggle the removal of threads after a x amount of days per forum. Disabled by default"""
		_key = "CLEANUPDAYS"
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


async def setup(bot: Bot) :
	await bot.add_cog(
		CleanUp(bot),
	)
