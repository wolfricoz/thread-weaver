import discord
from discord import app_commands
from discord.ext.commands import Cog, Bot


class General(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="archive_threads",
	                      description="Archives all threads in the specified TextChannel")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def archive_threads(self, interaction: discord.Interaction, channel: discord.TextChannel) :
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


async def setup(bot: Bot) :
	await bot.add_cog(
		General(bot),
	)
