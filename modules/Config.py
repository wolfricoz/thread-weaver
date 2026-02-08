import discord
from discord import app_commands
from discord.ext.commands import GroupCog, Bot
from discord_py_utilities.messages import send_message, send_response

from classes.discordcontrollers.forum.ForumPatternController import ForumPatternController
from classes.kernel.AccessControl import AccessControl
from classes.kernel.ConfigData import ConfigData
from database.transactions.ConfigTransactions import ConfigTransactions
from database.transactions.ForumCleanupTransactions import ForumCleanupTransactions


class Config(GroupCog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass

	def cog_unload(self) -> None:
		pass




async def setup(bot: Bot) :
	await bot.add_cog(
		Config(bot)
	)
