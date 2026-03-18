import asyncio
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.invites import create_invite
from discord_py_utilities.messages import send_response
from discord_py_utilities.permissions import find_first_accessible_text_channel

from classes.kernel.AccessControl import AccessControl
from classes.kernel.ConfigData import ConfigData
from data.env.loader import env, load_environment
from database.transactions.StaffTransactions import StaffTransactions
from resources.configs.ConfigMapping import ConfigMapping


async def send_modal(interaction, param, param1, param2) :
	pass


class Dev(GroupCog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="reload", description="reloads the current environment")
	async def reload_env(self, interaction: discord.Interaction):
		"""Reloads the environment variables from the .env file."""
		# A little challenge for you! Make it so this command can only be used by you.

		# reloads the env file.
		load_environment(override=True)
		await interaction.response.send_message(f"Your environment file has been reloaded! Your test variable is now: {env('TEST')}", ephemeral=True)



	@app_commands.command(name="add_staff", description="[DEV] Adds a user to the Banwatch staff team.")
	@app_commands.choices(role=[Choice(name=x, value=x.lower()) for x in ["Dev", "Rep"]])
	async def add_staff(self, interaction: discord.Interaction, user: discord.User, role: Choice[str]) :
		"""
		[DEV] Adds a user to the Banwatch staff with a specified role.

		**Permissions:**
		- `Bot Owner`
		"""
		if interaction.user.id != int(env("OWNER", 0)) :
			return await send_response(interaction, "You do not have permission to add staff members")
		StaffTransactions().add(user.id, role.value)
		await send_response(interaction, f"Staff member {user.mention} successfully added as a `{role.name}`!")
		AccessControl().reload()

	@app_commands.command(name="stop", description="[DEV] Shuts down the bot. Only the bot owner can use this.")
	async def quit(self, interaction: discord.Interaction) :
		"""
		[DEV] Shuts down the bot.

		**Permissions:**
		- `Bot Owner`
		"""
		if interaction.user.id != int(os.getenv("OWNER")) :
			return await send_response(interaction, "You do not have permission to add staff members")
		await send_response(interaction, "Shutting down", ephemeral=True)
		await self.bot.close()
		quit(0)

	@app_commands.command(name="remove_staff", description="[DEV] Removes a staff member from the Banwatch team.")
	@AccessControl().check_access("dev")
	async def remove_staff(self, interaction: discord.Interaction, user: discord.User) :
		"""
		[DEV] Removes a user from the Banwatch staff.

		**Permissions:**
		- `Developer`
		"""
		StaffTransactions().delete(user.id)
		await send_response(interaction, f"Staff member {user.mention} successfully removed!")
		AccessControl().reload()


	@app_commands.command(name="announce", description="[DEV] Send an announcement to all guild owners")
	@AccessControl().check_access("dev")
	async def announce(self, interaction: discord.Interaction) :
		message = await send_modal(interaction, "What is the announcement?", "Announcement", 1700)
		if interaction.user.id != 188647277181665280 :
			return
		bot = self.bot
		supportguild = bot.get_guild(bot.SUPPORTGUILD)
		support_invite = await create_invite(supportguild)
		announcement = (f"## BAN WATCH ANNOUNCEMENT"
		                f"\n{message}"
		                f"\n-# You can join our support server by [clicking here to join]({support_invite}). If you have any questions, errors or concerns, please open a ticket in the support server.")

		for guild in self.bot.guilds :
			try:
				await asyncio.sleep(0)
				channel = await ConfigData().get_channel(guild, ConfigMapping.CHANGE_LOG_CHANNEL)
				if not channel:
					channel = await find_first_accessible_text_channel(guild)
				await channel.send(announcement)
			except Exception as e :
				try :
					await guild.owner.send(
						f"Banwatch could not send the announcement to your modchannel in {guild.name}, please check the mod channel settings. You can setup your modchannel with: ```/config change option:Mod channel channel:```")
					await guild.owner.send(announcement)
				except Exception as e :
					await interaction.channel.send(f"Error sending to {guild}({guild.owner}): {e}")

	@app_commands.command(name="leave_server", description="[DEV] Leave a server")
	@AccessControl().check_access("dev")
	async def leave_server(self, interaction: discord.Interaction, guildid: int) :
		guild = self.bot.get_guild(guildid)
		await guild.leave()
		await send_response(interaction,f"Left {guild}")




async def setup(bot: Bot) :
	await bot.add_cog(
		Dev(bot),
	)
