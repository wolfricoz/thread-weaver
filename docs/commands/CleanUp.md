---
layout: default
title: CleanUp
parent: Commands
nav_order: 1
---

<h1>CleanUp</h1>
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


### `left`

**Usage:** `/cleanup left <operation>`

> Toggle the removal of threads from users that left. Disabled by default

Permissions:
- Manage guild
- Premium access

---

### `old`

**Usage:** `/cleanup old <operation> <days>`

> Toggle the removal of threads after a x amount of days per forum. Disabled by default

Permissions:
- Manage guild
- Premium access

---

### `regex`

**Usage:** `/cleanup regex <operation> <pattern> <days>`

> Toggle the removal of threads threads based on a regex, allowing for pings or other content to automatically be removed after x amount of days.

Permissions:
- Manage guild
- Premium access

---

