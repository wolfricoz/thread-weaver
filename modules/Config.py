import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.messages import send_response

from classes.kernel.ConfigData import ConfigData
from classes.kernel.config.utils import ConfigUtils
from classes.kernel.queue import Queue
from database.transactions.ConfigTransactions import ConfigTransactions
from resources.configs.ConfigMapping import channels, toggles


class Config(GroupCog, name="config", description="Commands for configuring the bot") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass
	@app_commands.command(name="channels", description="Configure the channels used by Forum Manager!")
	@app_commands.choices(option=[
		Choice(name=confkey, value=confkey) for confkey in channels
	])
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.guild_only()
	async def channel(self, interaction: discord.Interaction, option: Choice[str], channel: discord.TextChannel) :
		"""
		Channel configuration for Forum Manager. This command allows you to set the channels used by the bot for various features. For example, you can set the channel where the bot will log automod actions.

		**Permissions:**
		- `Manage Server`
		"""
		if not channel.permissions_for(interaction.guild.me).send_messages :
			return await send_response(interaction, f"❌ I need the `Send Messages` permission in {channel.mention} to set it as the {option.value} channel.")
		if not channel.permissions_for(interaction.guild.me).view_channel :
			return await send_response(interaction, f"❌ I need the `Read Messages` permission in {channel.mention} to set it as the {option.value} channel.")
		ConfigData().add_key(interaction.guild.id, option.value.upper(), channel.id, overwrite=True)
		await send_response(interaction, f"Set {option.name} to {channel.mention}")
		return None

	@app_commands.command(description="Allows you to enable or disable various features of the bot.")
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]],
	                      key=[Choice(name=x, value=x) for x in toggles])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""
        This command allows you to enable or disable various features of the bot.
        You can turn things on or off to best suit your server's needs.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		match action.value.upper() :
			case "ENABLED" :
				ConfigTransactions().toggle_add(interaction.guild.id, key.value, action.value.upper())

			case "DISABLED" :
				ConfigTransactions().toggle_add(interaction.guild.id, key.value, action.value.upper())
				if key.value == "send_join_message" :
					return send_response(interaction,
					                     f"The lobby welcome message has been disabled. Users will no longer receive a welcome message or the verification button in the lobby channel. To allow users to verify, please use the /lobby command in the channel.",
					                     ephemeral=True)
		Queue().add(
			ConfigUtils.log_change(interaction.guild, {key.value : action.value.upper()}, user_name=interaction.user.mention,
			                       ))
		return await send_response(interaction, f"{key.value} has been set to {action.value}", ephemeral=True)



async def setup(bot: Bot) :
	await bot.add_cog(
		Config(bot),
	)
