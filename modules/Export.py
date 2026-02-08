from discord.ext.commands import GroupCog, Bot


class Export(GroupCog, name="export") :

	def __init__(self, bot: Bot) :
		self.bot = bot

	pass

	# export commands here.

async def setup(bot: Bot) :
	await bot.add_cog(
		Export(bot),
	)
