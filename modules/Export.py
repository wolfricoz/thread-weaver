import logging

import discord
from discord import TextChannel, app_commands
from discord.ext.commands import Bot, GroupCog
from discord_py_utilities.messages import send_message

from classes.kernel.AccessControl import AccessControl
from classes.support.ThreadArchive import ThreadArchive
from classes.support.Transformers import ForumOption, TextChannelOption, ThreadOption
from views.buttons.ConfirmButtons import ConfirmButtons
DEBUG = True

class Export(GroupCog, name="export") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="thread", description="Creates an export of a specific thread")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def thread(self, interaction: discord.Interaction, thread: ThreadOption, delete: bool = False) :
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
		try:
			export_class = ThreadArchive(interaction.guild.name + "_" + thread.name, channel=thread)
		except Exception as e:
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)

			return

		await export_class.run()
		await self.send_file(export_class, interaction, thread, delete)


	@app_commands.command(name="threads", description="Creates an export of all threads from a specific channel")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def threads(self, interaction: discord.Interaction, channel: TextChannel) :
		"""
		Creates an export of all threads in a specific channel. This will create a .zip file containing the channel's threads messages and attachments. The file will be sent to the user who invoked the command.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		buttons = ConfirmButtons(
			confirm_message=f"Creating an export of `{channel.name}`, this may take a while... The results will be sent to your DMs")
		result = await buttons.send_confirmation(interaction,
		                                         f"Are you sure you want to export `{channel.name}`? This will create a .zip file containing the thread's messages and image attachments. if you delete the thread after export, non-image attachments may not work as they rely on the url provided by discord, which is deleted when the message/thread is deleted. Threads with a large amount of images may fail to export due to the size of the .zip file. If you have any issues with the export, please contact support.\n\n**note** Forums have a high chance of failing to export due to the large amount of messages and attachments they can contain. It is recommended to export individual threads within the forum instead of the entire forum to ensure a successful export.",
		                                         )
		if not result :
			logging.info(f"{interaction.user} cancelled the export of {channel.name}")
			return
		try:
			export_class = ThreadArchive(interaction.guild.name + "_" + channel.name, channel=channel)
			await export_class.run(threads_only=True)

		except Exception as e:
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)
			return
		await self.send_file(export_class, interaction, channel, False)

	@app_commands.command(name="forum", description="Creates an export of an entire forum")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def forum(self, interaction: discord.Interaction, forum: ForumOption) :
		"""
		Creates an export of a specific forum. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

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
		try:
			export_class = ThreadArchive(interaction.guild.name + "_" + forum.name, channel=forum)
			await export_class.run()

		except Exception as e:
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)
			return
		await self.send_file(export_class, interaction, forum, False)


	@app_commands.command(name="channel", description="Creates an export of an entire channel")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def channel(self, interaction: discord.Interaction, channel: TextChannelOption, channel_only: bool) -> None :
		"""
		Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		buttons = ConfirmButtons(
			confirm_message=f"Creating an export of `{channel.name}`, this may take a while... The results will be sent to your DMs")
		result = await buttons.send_confirmation(interaction,
		                                         f"Are you sure you want to export `{channel.name}`? This will create a .zip file containing the thread's messages and image attachments. if you delete the thread after export, non-image attachments may not work as they rely on the url provided by discord, which is deleted when the message/thread is deleted. Threads with a large amount of images may fail to export due to the size of the .zip file. If you have any issues with the export, please contact support.\n\n**note** Forums have a high chance of failing to export due to the large amount of messages and attachments they can contain. It is recommended to export individual threads within the forum instead of the entire forum to ensure a successful export.",
		                                         )
		if not result :
			logging.info(f"{interaction.user} cancelled the export of {channel.name}")
			return
		try:
			export_class = ThreadArchive(interaction.guild.name + "_" + channel.name, channel=channel)

			await export_class.run(channel_only=channel_only)

		except Exception as e:
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)

			return
		await self.send_file(export_class, interaction, channel, False)

	def build_export_embed(
			self,
			export_class: ThreadArchive,
			channel: discord.Thread | discord.TextChannel | discord.ForumChannel,
			website_details: dict | None = None,
	) -> discord.Embed :
		"""Builds the export summary embed. One field per stat, so it's easy to prune."""
		r = export_class.report()
		hb = export_class.human_bytes

		embed = discord.Embed(
			title=f"Export: {channel.name}",
			colour=discord.Colour.green(),
		)

		# --- Contents ---
		embed.add_field(name="Threads", value=f"{r['threads']:,}", inline=True)
		embed.add_field(name="Messages", value=f"{r['messages']:,}", inline=True)

		embed.add_field(name="Images", value=f"{r['images']:,}", inline=True)
		embed.add_field(name="Unique images", value=f"{r['images_unique']:,}", inline=True)
		embed.add_field(name="Embeds", value=f"{r['embeds']:,}", inline=True)

		embed.add_field(name="Other files", value=f"{r['links']:,}", inline=True)
		embed.add_field(name="Attachments", value=f"{r['attachments']:,}", inline=True)
		embed.add_field(name="\u200b", value="\u200b", inline=True)  # spacer, keeps the 3-column grid tidy
		embed.add_field(name="Archive size", value=f"**{hb(r['zip_bytes'])}**", inline=True)

		# --- Size ---
		if DEBUG :
			original = r["raw_bytes"] + r["dedup_saved"] + r["reencode_saved"]
			embed.add_field(name="Original size", value=hb(original), inline=True)
			embed.add_field(name="Total saved", value=f"−{hb(r['total_saved'])}", inline=True)

			embed.add_field(name="Saved: dedup", value=f"−{hb(r['dedup_saved'])}", inline=True)
			embed.add_field(name="Saved: re-encode", value=f"−{hb(r['reencode_saved'])}", inline=True)
			embed.add_field(name="Saved: zip", value=f"−{hb(r['zip_saved'])}", inline=True)

		# --- Range ---
		if r["first_message"] and r["last_message"] :
			embed.add_field(
				name="Covers",
				value=(
					f"<t:{int(r['first_message'].timestamp())}:D> → "
					f"<t:{int(r['last_message'].timestamp())}:D>"
				),
				inline=False,
			)

		# --- Delivery ---
		if website_details :
			embed.add_field(name="Download", value=f"[Click here]({website_details['link']})", inline=False)
			embed.add_field(name="Password", value=f"`{website_details['password']}`", inline=False)
			embed.set_footer(text=f"This link can only be used once · archived in {r['elapsed']:.1f}s")
		else :
			embed.set_footer(text=f"Archived in {r['elapsed']:.1f}s")

		return embed

	async def send_file(
			self,
			export_class: ThreadArchive,
			interaction: discord.Interaction,
			channel: discord.Thread | discord.TextChannel | discord.ForumChannel,
			delete: bool = False,
	) :
		"""
		:param export_class:
		:param interaction:
		:param channel:
		:param delete:
		:return:
		"""
		website_details = await export_class.upload()
		embed = self.build_export_embed(export_class, channel, website_details)

		try :
			if website_details :
				# too large for discord — it's on the download site instead
				await send_message(interaction.user, embed=embed)
			else :
				await send_message(
					interaction.user,
					embed=embed,
					files=[discord.File(export_class.zip_path)],
				)
		except discord.Forbidden :
			await send_message(
				interaction.channel,
				f"{interaction.user.mention}, I was unable to send you the export in DMs. "
				f"Please check your DM settings and try again.",
			)
		except Exception as e :
			await send_message(
				interaction.channel,
				f"{interaction.user.mention}, an error occurred while sending you the export: {e}",
			)
			logging.error(e, exc_info=True)
			await export_class.clean_up()
			return

		await export_class.clean_up()
		if not delete :
			return
		try :
			await channel.delete()
		except Exception as e :
			await send_message(
				interaction.channel,
				f"{interaction.user.mention}, an error occurred while deleting the thread: {e}",
				error_mode="ignore",
			)
			logging.error(e, exc_info=True)


async def setup(bot: Bot) :
	await bot.add_cog(
		Export(bot),
	)
