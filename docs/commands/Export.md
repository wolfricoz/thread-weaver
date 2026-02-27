---
layout: default
title: Export
parent: Commands
nav_order: 4
---

<h1>Export</h1>
<h6>version: 0.1</h6>
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

> Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

### `forum`

**Usage:** `/export forum <forum>`

> Creates an export of a specific thread. This will create a .zip file containing the thread's messages and attachments. The file will be sent to the user who invoked the command.

**Permissions:**
- `Manage Threads`
- `Premium Access`

---

