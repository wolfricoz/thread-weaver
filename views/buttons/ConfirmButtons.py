import discord
import discord_py_utilities.messages



class ConfirmButtons(discord.ui.View) :
	def __init__(self, confirm_message: str = "Confirmation Received") :
		super().__init__(timeout=None, )
		self.result = None
		self.confirm_message = confirm_message

	async def send_confirmation(self, interaction: discord.Interaction, message: str, confirm_message: str = "Confirmation Received") :
		await discord_py_utilities.messages.send_response(interaction, message, view=self, ephemeral=True)
		await self.wait()
		return self.result

	@discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="Confirm_action")
	async def Confirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""This is a button"""
		self.result = True
		await self.disable_buttons(interaction)
		await discord_py_utilities.messages.send_response(interaction, self.confirm_message, ephemeral=True)
		self.stop()

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="Cancel_action")
	async def Cancel(self, interaction: discord.Interaction, button: discord.ui.Button) :
		self.result = False
		await self.disable_buttons(interaction)
		await discord_py_utilities.messages.send_response(interaction, "Action cancelled", ephemeral=True)
		self.stop()


	async def disable_buttons(self, interaction: discord.Interaction) :
		for item in self.children :
			item.disabled = True
		try :
			await interaction.message.edit(view=self)
		except Exception :
			pass

	async def load_data(self, interaction: discord.Interaction) :
		"""Load data from embed"""
		if len(interaction.message.embeds) < 1 :
			return False
		return True
