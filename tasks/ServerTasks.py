import asyncio
import logging

from discord.ext import tasks
from discord.ext.commands import Bot, Cog
from discord_py_utilities.invites import check_guild_invites

from classes.dashboard.Servers import Servers
from classes.kernel.AccessControl import AccessControl
from database.transactions.ServerTransactions import ServerTransactions


class ServerTasks(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		# register tasks
		self.update_servers.start()

	def cog_unload(self) -> None:
		# unregister tasks
		self.update_servers.cancel()

	pass

	# this task will run every 30 minutes, you can change the time interval as needed!
	@tasks.loop(hours=1)
	async def update_servers(self) :
		# This is a sample task that runs every 30 minutes.
		logging.info("Updating server list...")
		count = 0

		# We set all the servers to inactive, this way we don't have to loop through the database and check which servers are still active.
		ServerTransactions().set_all_inactive()

		# Main loop of this function, it loops through all the servers the bot is in and updates the database with the current information. If the server is not in the database, it adds it.
		for guild in self.bot.guilds :
			if count % 10 == 0 :
				logging.info(f"Updated {count} servers...")
				await asyncio.sleep(0) # prevents blocking the event loop for too long
			count += 1
			db_guild = ServerTransactions().get(guild.id)
			try:
				if not db_guild:
					logging.info(f"Adding {guild.name} to the database...")
					ServerTransactions().add(guild.id, guild.owner.name , guild.name, guild.member_count, await check_guild_invites(self.bot, guild, "invalid"), active=True)
					continue
				ServerTransactions().update(
					guild.id,
					guild.owner.name,
					guild.name,
					guild.member_count,
					await check_guild_invites(self.bot, guild, db_guild.invite),
					owner_id=guild.owner.id,
					active=True
				)
			except Exception as e:
				logging.error(f"Failed to update {guild.name}: {e}", exc_info=True)
				continue
		# sync all the active servers with the dashboard
		guilds = ServerTransactions().get_all(id_only=False)
		await Servers().update_servers(guilds)
		AccessControl().reload()
		logging.info(f"Updated {count} servers!")







	@update_servers.before_loop
	async def before_update_servers(self) :
		# Wait until the bot is ready before starting the task
		await self.bot.wait_until_ready()

async def setup(bot: Bot) :
	await bot.add_cog(
		ServerTasks(bot),
	)
