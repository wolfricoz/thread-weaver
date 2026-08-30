"""Permission notice system.

Tells a Discord server, in plain language, when Thread Weaver is missing the
permissions it needs to work, and how to fix it. Self-contained apart from a
ConfigData lookup for the mod/log channel, so it ports between bots.

Design pattern (keep these invariants if you change this file):
- Always name the **server + channel** in the text. Owners run many servers,
  and channel/role mentions do not render inside DMs, so use plain names.
- Deliver guild-first: configured mod channel -> any accessible guild channel
  -> the invoking user's DM -> the guild owner's DM.
- Send an **embed OR plain text** depending on the `embed_links` permission of
  the target, never both.
- Attach the documentation links as **buttons** so they survive when
  `embed_links` is missing.
- **Throttle by source**: commands notify every time; loops/events notify at
  most once per hour per distinct problem.
- Human-readable labels + numbered fix steps. This notifier **must never
  raise**. Dependencies are **lazy-imported** to dodge circular imports.
"""
import logging
import os
import time

import discord
from discord_py_utilities.messages import send_message
from discord_py_utilities.permissions import (
	check_missing_channel_permissions,
	check_missing_guild_permissions,
	find_first_accessible_text_channel,
)

from classes.support.singleton import Singleton
from project.data import BOT_NAME

# Link shown on the "Setup Guide" button. Override per deployment with the
# PERMISSIONS_GUIDE_URL env var.
GUIDE_URL = os.getenv("PERMISSIONS_GUIDE_URL", "https://wolfricoz.github.io/thread-weaver/")
# Official Discord permissions FAQ. Stable URL, always safe to link.
DISCORD_FAQ_URL = "https://support.discord.com/hc/en-us/articles/206029707"

# Throttle window for loop/event-sourced notices, in seconds.
THROTTLE_SECONDS = 3600

# The core permissions Thread Weaver needs to function guild-wide.
CORE_GUILD_PERMISSIONS = [
	"view_channel",
	"read_message_history",
	"send_messages",
	"send_messages_in_threads",
	"embed_links",
	"manage_messages",
	"manage_threads",
]

# Human-readable labels for the permissions the bot actually asks for.
PERMISSION_LABELS = {
	"view_channel"            : "View Channel",
	"read_message_history"    : "Read Message History",
	"send_messages"           : "Send Messages",
	"send_messages_in_threads": "Send Messages in Threads",
	"embed_links"             : "Embed Links",
	"attach_files"            : "Attach Files",
	"add_reactions"           : "Add Reactions",
	"manage_messages"         : "Manage Messages",
	"manage_threads"          : "Manage Threads",
	"manage_channels"         : "Manage Channels",
}


def humanise(perms: list[str]) -> list[str] :
	"""Turns raw permission attribute names into readable labels."""
	return [PERMISSION_LABELS.get(p, p.replace("_", " ").title()) for p in perms]


class PermissionNotice(metaclass=Singleton) :
	"""Sends 'the bot is missing permissions' notices, guild-first, throttled."""

	# {(guild_id, problem_key): last_sent_monotonic}
	_last_sent: dict = {}

	async def notify(self, guild: discord.Guild, missing: list[str], *,
	                 channel: discord.abc.GuildChannel | None = None,
	                 source: str = "event",
	                 user: discord.User | discord.Member | None = None) -> None :
		"""Notify a guild that the bot is missing `missing` permissions.

		:param guild: the guild that is missing permissions.
		:param missing: raw permission attribute names (e.g. ["manage_threads"]).
		:param channel: the specific channel the problem is about, if any. Named
		                in the message so owners know where to look.
		:param source: "command" notifies every time; "event"/"loop" throttle to
		               once per hour per distinct problem.
		:param user: the user who triggered the action, used as a DM fallback.
		"""
		try :
			if guild is None or not missing :
				return
			# De-duplicate while preserving order.
			perms = list(dict.fromkeys(missing))
			problem_key = f"{channel.id if channel else 'guild'}:{','.join(sorted(perms))}"
			if not self._should_send(guild.id, problem_key, source) :
				return

			target, allow_embed = await self._resolve_target(guild, channel, user)
			if target is None :
				logging.warning("PermissionNotice: no delivery target for %s (%s)", guild.name, guild.id)
				return

			view = self._build_view()
			if allow_embed :
				await send_message(target, embed=self._build_embed(guild, perms, channel), view=view,
				                   error_mode="ignore")
			else :
				await send_message(target, self._build_text(guild, perms, channel), view=view, error_mode="ignore")
		except Exception as e :
			# A notifier must never take down its caller.
			logging.error("PermissionNotice failed for %s: %s", getattr(guild, "id", "?"), e, exc_info=True)

	async def check_guild(self, guild: discord.Guild, *, source: str = "loop",
	                      user: discord.User | discord.Member | None = None) -> list[str] :
		"""Check the bot's guild-wide permissions and notify if any are missing.

		Returns the list of missing permissions (empty if all present).
		"""
		missing = check_missing_guild_permissions(guild, CORE_GUILD_PERMISSIONS) or []
		if missing :
			await self.notify(guild, missing, source=source, user=user)
		return missing

	# == throttling ==

	def _should_send(self, guild_id: int, problem_key: str, source: str) -> bool :
		"""Commands always send; loops/events send once per hour per problem."""
		if source == "command" :
			return True
		key = (guild_id, problem_key)
		now = time.monotonic()
		last = self._last_sent.get(key)
		if last is not None and now - last < THROTTLE_SECONDS :
			return False
		self._last_sent[key] = now
		return True

	# == delivery target resolution (guild-first cascade) ==

	async def _resolve_target(self, guild: discord.Guild, channel, user) :
		"""Resolve where to send: mod channel -> any channel -> user DM -> owner DM.

		Returns (target, allow_embed).
		"""
		# 1. Configured mod/log channel. Lazy-imported to avoid circular imports.
		try :
			from classes.kernel.ConfigData import ConfigData
			from resources.configs.ConfigMapping import ConfigMapping
			mod = await ConfigData().get_channel(guild, ConfigMapping.AUTOMOD_LOG, optional=True)
			if mod is not None and self._can_send(mod) :
				return mod, self._can_embed(mod)
		except Exception as e :
			logging.debug("PermissionNotice: mod channel lookup failed for %s: %s", guild.id, e)

		# 2. Any accessible text channel in the guild.
		fallback = find_first_accessible_text_channel(guild)
		if fallback is not None :
			return fallback, self._can_embed(fallback)

		# 3. The invoking user's DM (embeds always allowed in DMs).
		if user is not None :
			return user, True

		# 4. The guild owner's DM.
		if guild.owner is not None :
			return guild.owner, True

		return None, True

	@staticmethod
	def _can_send(ch: discord.abc.GuildChannel) -> bool :
		return not check_missing_channel_permissions(ch, ["view_channel", "send_messages"])

	@staticmethod
	def _can_embed(ch: discord.abc.GuildChannel) -> bool :
		return not check_missing_channel_permissions(ch, ["embed_links"])

	# == message building ==

	def _build_body(self, guild: discord.Guild, perms: list[str], channel, *, header: bool) -> str :
		"""Build the notice text. `header` adds a bold title line for plain-text."""
		labels = humanise(perms)
		where = f" (specifically in #{channel.name})" if channel is not None else ""
		lines = []
		if header :
			lines += [f"⚠️ **{BOT_NAME} is missing permissions in {guild.name}**", ""]
		lines += [
			f"{BOT_NAME} can't work properly in **{guild.name}**{where} because it's missing the "
			f"permission(s) below. (Channel and role mentions don't show in DMs, so names are used.)",
			"",
			"**Missing permissions:**",
		]
		lines += [f"• {label}" for label in labels]
		lines += [
			"",
			"**How to fix it:**",
			f"1. Open **Server Settings → Roles → {BOT_NAME}**"
			+ (f", or edit permissions directly on **#{channel.name}**." if channel is not None else "."),
			f"2. Enable: {', '.join(labels)}.",
			f"3. For threads, make sure the **{BOT_NAME}** role has **Manage Threads** and sits above the "
			f"roles and threads it manages.",
			"4. Then re-run the command, or wait for the next automatic check.",
		]
		return "\n".join(lines)

	def _build_text(self, guild: discord.Guild, perms: list[str], channel) -> str :
		return self._build_body(guild, perms, channel, header=True)

	def _build_embed(self, guild: discord.Guild, perms: list[str], channel) -> discord.Embed :
		return discord.Embed(
			title=f"⚠️ {BOT_NAME} is missing permissions in {guild.name}",
			description=self._build_body(guild, perms, channel, header=False),
			colour=discord.Colour.orange(),
		)

	def _build_view(self) -> discord.ui.View | None :
		"""Doc links as buttons so they survive missing embed_links."""
		view = discord.ui.View(timeout=None)
		added = False
		if isinstance(GUIDE_URL, str) and GUIDE_URL.startswith("http") :
			view.add_item(discord.ui.Button(label="Setup Guide", style=discord.ButtonStyle.link, url=GUIDE_URL))
			added = True
		if isinstance(DISCORD_FAQ_URL, str) and DISCORD_FAQ_URL.startswith("http") :
			view.add_item(
				discord.ui.Button(label="Discord: Permissions FAQ", style=discord.ButtonStyle.link, url=DISCORD_FAQ_URL))
			added = True
		return view if added else None
