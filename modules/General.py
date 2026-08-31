import logging
import os

import discord
from discord import app_commands
from discord.ext.commands import Cog, Bot

from classes.support.Transformers import TextChannelOption
from database.transactions.ServerTransactions import ServerTransactions

# Published in docs/privacypolicy.md; keep the two in step.
PRIVACY_EMAIL = "rico@strykerdevelopment.com"
PRIVACY_POLICY_URL = "https://wolfricoz.github.io/thread-weaver/privacypolicy"


class General(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="archive_threads",
	                      description="Archives all threads in the specified TextChannel")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def archive_threads(self, interaction: discord.Interaction, channel: TextChannelOption) :
		"""
		Archives all threads in the specified TextChannel.

		**Permissions:**
		- Requires `Manage Guild` permission.
		"""
		await interaction.response.defer(ephemeral=True)
		count = 0
		for thread in channel.threads :
			if thread.archived :
				continue
			await thread.edit(archived=True)
			count += 1
		await interaction.followup.send(f"Archived {count} threads in {channel.mention}.")

	def support_invite(self) -> str | None :
		"""Returns the support server's invite, or None if it isn't available."""
		guild_id = os.getenv("GUILD")
		if not guild_id :
			return None
		try :
			support_server = ServerTransactions().get(int(guild_id))
		except (TypeError, ValueError) as e :
			logging.warning(f"Could not resolve the support server for the privacy command: {e}")
			return None
		if support_server is None or not support_server.invite :
			return None
		return support_server.invite

	@app_commands.command(name="privacy",
	                      description="What data Forum Manager holds, and how to request its deletion")
	async def privacy(self, interaction: discord.Interaction) :
		"""
		Shows what data Forum Manager holds about you and how to have it removed.

		**Permissions:**
		- None, available to everyone.
		"""
		embed = discord.Embed(
			title="Your data and Forum Manager",
			description=(
				"Forum Manager checks posts against the rules this server's staff configured, in the forum "
				"channels they registered. **The text of your messages is not stored** — it is checked and "
				"discarded. Your data is never used to train AI models, and is never sold or shared."
			),
			colour=discord.Colour.purple(),
		)
		embed.add_field(
			name="What we do store",
			value=(
				"Per-server settings, and the Discord ID of the server's owner. No per-member records, no "
				"message content, and no tracking of anyone between servers."
			),
			inline=False,
		)
		embed.add_field(
			name="Requesting deletion of your data",
			value=(
				f"Open a ticket in our support server, or email `{PRIVACY_EMAIL}`. We respond within 30 days.\n\n"
				"If you run a server: removing Forum Manager deletes its configuration immediately, and the "
				"record is permanently erased 30 days later."
			),
			inline=False,
		)

		view = discord.ui.View()
		view.add_item(discord.ui.Button(label="Privacy Policy", style=discord.ButtonStyle.link,
		                                url=PRIVACY_POLICY_URL))
		invite = self.support_invite()
		if invite :
			view.add_item(discord.ui.Button(label="Support Server", style=discord.ButtonStyle.link, url=invite))

		await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: Bot) :
	await bot.add_cog(
		General(bot),
	)
