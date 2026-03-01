---
layout: default
title: Config
parent: Commands
nav_order: 2
---

<h1>Config</h1>
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


### `channel`

**Usage:** `/config channel <option> <channel>`

> Channel configuration for Forum Manager. This command allows you to set the channels used by the bot for various features. For example, you can set the channel where the bot will log automod actions.

**Permissions:**
- `Manage Server`

---

### `toggles`

**Usage:** `/config toggles <key> <action>`

> This command allows you to enable or disable various features of the bot.
You can turn things on or off to best suit your server's needs.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

