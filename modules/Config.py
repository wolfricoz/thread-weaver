from discord.ext.commands import GroupCog, Bot


class Config(GroupCog, name="config", description="Commands for configuring the bot") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass


async def setup(bot: Bot) :
	await bot.add_cog(
		Config(bot),
	)
