---
layout: default
title: Export
parent: Commands
nav_order: 4
---

<h1>Export</h1>
<h6>version: 0.5: Alpha</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Represents a cog that also doubles as a parent :class:`discord.app_commands.Group` for
the application commands defined within it.

This inherits from :class:`Cog` and the options in :class:`CogMeta` also apply to this.
See the :class:`Cog` documentation for methods.

Decorators such as :func:`~discord.app_commands.guild_only`, :func:`~discord.app_commands.guilds`,
and :func:`~discord.app_commands.default_permissions` will apply to the group if used on top of the
cog.

Hybrid commands will also be added to the Group, giving the ability to categorize slash commands into
groups, while keeping the prefix-style command as a root-level command.

For example:

.. code-block:: python3

    from discord import app_commands
    from discord.ext import commands

    @app_commands.guild_only()
    class MyCog(commands.GroupCog, group_name='my-cog'):
        pass

.. versionadded:: 2.0


### `thread`

**Usage:** `/export thread <thread> <delete>`

> Creates an export of a single thread. This will create a .zip file containing the thread's messages and image attachments. The file will be sent to the user who invoked the command via DM.

**Parameters:**
- `thread`: The thread to export.
- `delete`: Whether to delete the thread once the export has been sent. Defaults to `False`.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

### `threads`

**Usage:** `/export threads <channel>`

> Creates an export of every thread in a specific text channel. The channel's own messages are skipped; only its threads are archived. This will create a .zip file containing those threads' messages and image attachments. The file will be sent to the user who invoked the command via DM.

**Parameters:**
- `channel`: The text channel whose threads should be exported.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

### `forum`

**Usage:** `/export forum <forum>`

> Creates an export of an entire forum, including every thread it contains. This will create a .zip file containing those threads' messages and image attachments. The file will be sent to the user who invoked the command via DM.

**Parameters:**
- `forum`: The forum channel to export.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

### `channel`

**Usage:** `/export channel <channel> <channel_only>`

> Creates an export of a specific text channel. This will create a .zip file containing the channel's messages and image attachments. The file will be sent to the user who invoked the command via DM.

**Parameters:**
- `channel`: The text channel to export.
- `channel_only`: When `True`, only the channel's own messages are exported. When `False`, the channel's threads are included as well.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

### `build_export_embed`

**Usage:** `/export build_export_embed <export_class> <channel> <website_details>`

> Builds the export summary embed. One field per stat, so it's easy to prune.

---

### `send_file`

**Usage:** `/export send_file <export_class> <channel> <delete>`

> Uploads the finished archive, sends the summary embed to the user who invoked the command, then cleans up the temporary files.

If the archive is too large for Discord it is uploaded to the download site and only a link is DMed. If the DM cannot be delivered, a fallback message is sent in the channel the command was used in.

:param export_class: The completed ThreadArchive holding the generated .zip.
:param interaction: The interaction that triggered the export; used for the target user and the fallback channel.
:param channel: The thread, channel or forum that was exported; used for the embed title and for the optional deletion.
:param delete: Whether to delete `channel` once the export has been sent. Defaults to `False`.
:return: None

---

### `category`

**Usage:** `/export category <category> <channel_only> <threads_only>`

> Creates an export of every channel in a category. Each channel is archived separately, producing one .zip file per channel containing that channel's messages and image attachments. Each file will be sent to the user who invoked the command via DM.

**Parameters:**
- `category`: The category whose channels should be exported.
- `channel_only`: When `True`, only each channel's own messages are exported. When `False`, their threads are included as well.
- `thread_only`: Currently has no effect; it is not passed through to the archiver.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

