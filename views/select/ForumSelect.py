import discord.ui
from discord.ui import ChannelSelect
from discord_py_utilities.messages import send_response


class ForumSelect(discord.ui.View) :

	def __init__(self, timeout: float = 180, keep_interaction: bool = False) :
		super().__init__(timeout=timeout)
		self.interaction = None
		self.selected_channels = []
		self.keep_interaction = keep_interaction

	@discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.forum], min_values=1, max_values=25,
	                   placeholder="Select your forum channels here")
	async def select_channels(self, interaction: discord.Interaction, select: ChannelSelect) :
		self.selected_channels = select.values
		channel_mentions = ", ".join(channel.mention for channel in self.selected_channels)
		if not self.keep_interaction:
			await send_response(
				interaction,
				f"You have selected the following forum channel(s): {channel_mentions}",
				ephemeral=True
			)
		self.interaction = interaction
		self.stop()
