"""Creates a custom warning modal for the bot."""
import logging

import discord


class InputModal(discord.ui.Modal):
    custom_id = "InputModal"

    def __init__(self, confirmation, title, input_label = 'What is the reason?', placeholder = 'Type your reason here...', max_length = 500, ephemeral = True):
        super().__init__(timeout=None, title=title)  # Set a timeout for the modal
        self.confirmation = confirmation
        self.ephemeral = ephemeral
        reason = discord.ui.TextInput(label='What is the reason?', style=discord.TextStyle.long, placeholder='Type your reason here...', max_length=500)
        self.add_item(reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            await self.send_message(interaction, self.confirmation)
        except discord.errors.HTTPException:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await self.send_message(interaction, f"An error occurred: {error}")

    async def send_message(self, interaction: discord.Interaction, message: str) -> None:
        """sends the message to the channel."""
        try:
            await interaction.response.send_message(message, ephemeral=self.ephemeral)
        except discord.errors.HTTPException:
            pass
        except Exception as e:
            logging.error(e)


async def send_modal(interaction: discord.Interaction, confirmation, title = 'Input Modal', max_length=500, ephemeral = True):
    """Sends the modal to the channel."""
    view = InputModal(confirmation, title, ephemeral)
    view.reason.max_length = max_length
    await interaction.response.send_modal(view)

    await view.wait()
    return view.reason.value


import logging
import discord


class InputModal(discord.ui.Modal) :
    """A reusable modal for capturing text input."""

    def __init__(self, title: str, label: str, placeholder: str, max_length: int, ephemeral: bool) :
        super().__init__(title=title, timeout=None)
        self.ephemeral = ephemeral

        # Assign to self so it can be accessed later
        self.input_field = discord.ui.TextInput(
            label=label,
            style=discord.TextStyle.long,
            placeholder=placeholder,
            max_length=max_length,
            required=True
        )
        self.add_item(self.input_field)
        self.value = None  # To store the result

    async def on_submit(self, interaction: discord.Interaction) :
        self.value = self.input_field.value
        # If no interaction has been responded to, we must acknowledge it
        await interaction.response.defer(ephemeral=self.ephemeral)
        self.stop()  # Stops the modal 'listener'

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
        logging.error(f"Modal Error: {error}", exc_info=True)
        if not interaction.response.is_done() :
            await interaction.response.send_message("An error occurred while processing your input.", ephemeral=True)


async def get_input(
    interaction: discord.Interaction,
    title: str = "Input Required",
    label: str = "Reason",
    placeholder: str = "Type here...",
    max_length: int = 500,
    ephemeral: bool = True
) -> str | None :
    """Sends a modal and returns the user input string, or None if they cancel."""
    modal = InputModal(title, label, placeholder, max_length, ephemeral)
    await interaction.response.send_modal(modal)

    # This waits until on_submit or a timeout occurs
    await modal.wait()
    return modal.value