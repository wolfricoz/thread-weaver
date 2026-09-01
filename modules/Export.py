import logging

import discord
from discord import CategoryChannel, TextChannel, app_commands
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
		Creates an export of a single thread. This will create a .zip file containing the thread's messages and image attachments. The file will be sent to the user who invoked the command via DM.

		**Parameters:**
		- `thread`: The thread to export.
		- `delete`: Whether to delete the thread once the export has been sent. Defaults to `False`.

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
		try :
			export_class = ThreadArchive(interaction.guild.name + "_" + thread.name, channel=thread)
		except Exception as e :
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
		Creates an export of every thread in a specific text channel. The channel's own messages are skipped; only its threads are archived. This will create a .zip file containing those threads' messages and image attachments. The file will be sent to the user who invoked the command via DM.

		**Parameters:**
		- `channel`: The text channel whose threads should be exported.

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
		try :
			export_class = ThreadArchive(interaction.guild.name + "_" + channel.name, channel=channel)
			await export_class.run(threads_only=True)

		except Exception as e :
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)
			return
		await self.send_file(export_class, interaction, channel, False)

	@app_commands.command(name="forum", description="Creates an export of an entire forum")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def forum(self, interaction: discord.Interaction, forum: ForumOption) :
		"""
		Creates an export of an entire forum, including every thread it contains. This will create a .zip file containing those threads' messages and image attachments. The file will be sent to the user who invoked the command via DM.

		**Parameters:**
		- `forum`: The forum channel to export.

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
		try :
			export_class = ThreadArchive(interaction.guild.name + "_" + forum.name, channel=forum)
			await export_class.run()

		except Exception as e :
			await send_message(interaction.user, f"Failed to create archive: {e}")
			logging.error(e, exc_info=True)
			return
		await self.send_file(export_class, interaction, forum, False)

	@app_commands.command(name="channel", description="Creates an export of an entire channel")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def channel(self, interaction: discord.Interaction, channel: TextChannelOption, channel_only: bool) -> None :
		"""
		Creates an export of a specific text channel. This will create a .zip file containing the channel's messages and image attachments. The file will be sent to the user who invoked the command via DM.

		**Parameters:**
		- `channel`: The text channel to export.
		- `channel_only`: When `True`, only the channel's own messages are exported. When `False`, the channel's threads are included as well.

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
		try :
			export_class = ThreadArchive(interaction.guild.name + "_" + channel.name, channel=channel)

			await export_class.run(channel_only=channel_only)

		except Exception as e :
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
		Uploads the finished archive, sends the summary embed to the user who invoked the command, then cleans up the temporary files.

		If the archive is too large for Discord it is uploaded to the download site and only a link is DMed. If the DM cannot be delivered, a fallback message is sent in the channel the command was used in.

		:param export_class: The completed ThreadArchive holding the generated .zip.
		:param interaction: The interaction that triggered the export; used for the target user and the fallback channel.
		:param channel: The thread, channel or forum that was exported; used for the embed title and for the optional deletion.
		:param delete: Whether to delete `channel` once the export has been sent. Defaults to `False`.
		:return: None
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

	@app_commands.command(name="category", description="Creates an export of an entire category")
	@app_commands.checks.has_permissions(manage_threads=True)
	@AccessControl().check_premium()
	async def category(self, interaction: discord.Interaction, category: CategoryChannel, channel_only: bool,
	                   threads_only: bool) -> None :
		"""
		Creates an export of every channel in a category. Each channel is archived separately, producing one .zip file per channel containing that channel's messages and image attachments. Each file will be sent to the user who invoked the command via DM.

		**Parameters:**
		- `category`: The category whose channels should be exported.
		- `channel_only`: When `True`, only each channel's own messages are exported. When `False`, their threads are included as well.
		- `thread_only`: Currently has no effect; it is not passed through to the archiver.

		**Permissions:**
		- `Manage Threads`
		- `Premium Access`
		"""
		buttons = ConfirmButtons(
			confirm_message=f"Creating an export of `{category.name}`, this may take a while... The results will be sent to your DMs")
		result = await buttons.send_confirmation(interaction,
		                                         f"Are you sure you want to export `{category.name}`? This will create a .zip file containing the thread's messages and image attachments. if you delete the thread after export, non-image attachments may not work as they rely on the url provided by discord, which is deleted when the message/thread is deleted. Threads with a large amount of images may fail to export due to the size of the .zip file. If you have any issues with the export, please contact support.\n\n**note** Forums have a high chance of failing to export due to the large amount of messages and attachments they can contain. It is recommended to export individual threads within the forum instead of the entire forum to ensure a successful export.",
		                                         )
		if not result :
			logging.info(f"{interaction.user} cancelled the export of {category.name}")
			return
		channel: discord.TextChannel
		for channel in category.channels :
			export_class = ThreadArchive(interaction.guild.name + "_" + channel.name, channel=channel)
			try :
				await export_class.run(channel_only=channel_only, threads_only=threads_only)
			except Exception as e :
				await send_message(interaction.user, f"Failed to create archive: {e}")
				logging.error(e, exc_info=True)
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
		Uploads the finished archive, sends the summary embed to the user who invoked the command, then cleans up the temporary files.

		If the archive is too large for Discord it is uploaded to the download site and only a link is DMed. If the DM cannot be delivered, a fallback message is sent in the channel the command was used in.

		:param export_class: The completed ThreadArchive holding the generated .zip.
		:param interaction: The interaction that triggered the export; used for the target user and the fallback channel.
		:param channel: The thread, channel or forum that was exported; used for the embed title and for the optional deletion.
		:param delete: Whether to delete `channel` once the export has been sent. Defaults to `False`.
		:return: None
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
