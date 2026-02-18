import logging

import discord
from discord import app_commands
from discord.ext.commands import Bot, GroupCog
from discord_py_utilities.messages import send_message

from classes.kernel.AccessControl import AccessControl
from classes.support.ThreadArchive import ThreadArchive
from views.buttons.ConfirmButtons import ConfirmButtons


class Export(GroupCog, name="export") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="thread", description="Creates an export of a specific thread")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def thread(self, interaction: discord.Interaction, thread: discord.Thread, delete: bool = False) :
		"""
		Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		buttons = ConfirmButtons(
			confirm_message=f"Creating an export of `{thread.name}`, this may take a while... The results will be sent to your DMs")
		result = await buttons.send_confirmation(interaction,
		                                         f"Are you sure you want to export `{thread.name}`? This will create a .zip file containing the thread's messages and image attachments. if you delete the thread after export, non-image attachments may not work as they rely on the url provided by discord, which is deleted when the message/thread is deleted. Threads with a large amount of images may fail to export due to the size of the .zip file. If you have any issues with the export, please contact support.",
		                                         )
		if not result :
			logging.info(f"{interaction.user} cancelled the export of {thread.name}")
			return
		export_class = ThreadArchive(interaction.guild.name + "_" + thread.name, channel=thread)
		await export_class.run()
		try :
			await send_message(interaction.user, f"Here is your export of `{thread.name}`:",
			                   files=[discord.File(export_class.zip_path)])
		except discord.Forbidden :
			await send_message(interaction.channel,
			                   f"{interaction.user.mention}, I was unable to send you the export in DMs. Please check your DM settings and try again.")
		except Exception as e :
			await send_message(interaction.user,
			                   f"{interaction.user.mention}, an error occurred while sending you the export: {e}")
			logging.error(e, exc_info=True)
			return
		await export_class.clean_up()
		if not delete :
			return
		try :
			await thread.delete()
		except Exception as e :
			await send_message(interaction.channel,
			                   f"{interaction.user.mention}, an error occurred while deleting the thread: {e}",
			                   error_mode="ignore")
			logging.error(e, exc_info=True)

	@app_commands.command(name="forum", description="Creates an export of an entire forum")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def forum(self, interaction: discord.Interaction, forum: discord.ForumChannel) :
		"""
		Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		buttons = ConfirmButtons(
			confirm_message=f"Creating an export of `{forum.name}`, this may take a while... The results will be sent to your DMs")
		result = await buttons.send_confirmation(interaction,
		                                         f"Are you sure you want to export `{forum.name}`? This will create a .zip file containing the thread's messages and image attachments. if you delete the thread after export, non-image attachments may not work as they rely on the url provided by discord, which is deleted when the message/thread is deleted. Threads with a large amount of images may fail to export due to the size of the .zip file. If you have any issues with the export, please contact support.\n\n**note** Forums have a high chance of failing to export due to the large amount of messages and attachments they can contain. It is recommended to export individual threads within the forum instead of the entire forum to ensure a successful export.",
		                                         )
		if not result :
			logging.info(f"{interaction.user} cancelled the export of {forum.name}")
			return
		export_class = ThreadArchive(interaction.guild.name + "_" + forum.name, channel=forum)
		await export_class.run()
		try :
			await send_message(interaction.user, f"Here is your export of `{forum.name}`:",
			                   files=[discord.File(export_class.zip_path)])
		except discord.Forbidden :
			await send_message(interaction.channel,
			                   f"{interaction.user.mention}, I was unable to send you the export in DMs. Please check your DM settings and try again.")
		except Exception as e :
			await send_message(interaction.user,
			                   f"{interaction.user.mention}, an error occurred while sending you the export: {e}")
			logging.error(e, exc_info=True)
			return
		await export_class.clean_up()


async def setup(bot: Bot) :
	await bot.add_cog(
		Export(bot),
	)
