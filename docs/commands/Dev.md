---
layout: default
title: Dev
parent: Commands
nav_order: 3
---

<h1>Dev</h1>
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


### `reload_env`

**Usage:** `/dev reload_env`

> Reloads the environment variables from the .env file.

---

### `add_staff`

**Usage:** `/dev add_staff <user> <role>`

> [DEV] Adds a user to the Banwatch staff with a specified role.

**Permissions:**
- `Bot Owner`

---

### `quit`

**Usage:** `/dev quit`

> [DEV] Shuts down the bot.

**Permissions:**
- `Bot Owner`

---

### `remove_staff`

**Usage:** `/dev remove_staff <user>`

> [DEV] Removes a user from the Banwatch staff.

**Permissions:**
- `Developer`

---

