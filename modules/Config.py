import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.messages import send_response

from classes.kernel.ConfigData import ConfigData
from resources.configs.ConfigMapping import channels


class Config(GroupCog, name="config", description="Commands for configuring the bot") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass

	# TODO: setup channels:
	# Automod log channel

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



async def setup(bot: Bot) :
	await bot.add_cog(
		Config(bot),
	)
