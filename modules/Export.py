import logging

import discord
from discord import app_commands
from discord.ext.commands import Bot, GroupCog
from discord_py_utilities.messages import send_message, send_response

from classes.kernel.AccessControl import AccessControl
from classes.support.ThreadArchive import ThreadArchive


class Export(GroupCog, name="export") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="thread", description="Creates an export of a specific thread")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def thread(self, interaction: discord.Interaction, thread: discord.Thread) :
		"""
		Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		await send_response(interaction, f"Creating an export of `{thread.name}`, this may take a while... The results will be sent to your DMs", ephemeral=True)
		export_class = ThreadArchive(interaction.guild.name + "_" + thread.name, channel=thread)
		await export_class.run()
		try:
			await send_message(interaction.user, f"Here is your export of `{thread.name}`:", files=[discord.File(export_class.zip_path)])
		except discord.Forbidden:
			await send_message(interaction.channel, f"{interaction.user.mention}, I was unable to send you the export in DMs. Please check your DM settings and try again.")
		except Exception as e:
			await send_message(interaction.user, f"{interaction.user.mention}, an error occurred while sending you the export: {e}")
			logging.error(e, exc_info=True)
		await export_class.clean_up()



async def setup(bot: Bot) :
	await bot.add_cog(
		Export(bot),
	)
