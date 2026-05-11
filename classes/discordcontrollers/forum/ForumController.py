import discord
from discord_py_utilities.messages import send_response

from views.select.ForumSelect import ForumSelect


class ForumController():

	@staticmethod
	async def select_forums(interaction: discord.Interaction, response: str, keep_interaction: bool = False) -> tuple :
		"""
		"""
		forumselect = ForumSelect(keep_interaction=keep_interaction)
		await send_response(interaction, response, view=forumselect, ephemeral=True)
		await forumselect.wait()
		return forumselect.selected_channels, forumselect.interaction