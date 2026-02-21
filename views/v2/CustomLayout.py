import discord


class CustomLayout(discord.ui.LayoutView) :
	"""This is the 2.0 embed layout for onboarding messages."""

	def __init__(self, layout: list) :
		super().__init__(timeout=None)
		for item in layout:
			self.add_item(item)


	custom_id = "custom_layout"


