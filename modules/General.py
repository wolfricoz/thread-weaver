from discord.ext.commands import Cog, Bot


class General(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass


async def setup(bot: Bot) :
	await bot.add_cog(
		General(bot),
	)
