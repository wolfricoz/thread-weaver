# Cleanup:
# CLEANUPLEFT
# CLEANUPDAYS
# CLEANUPREGEX (regex goes in extra)
from enum import StrEnum


class ConfigMapping(StrEnum) :
	"""This is the mapping for the config keys, this way we can avoid typos and have a single source of truth for the config keys."""

	# === Automod ===
	AUTOMOD_LOG = "AUTOMOD_LOG"
	AUTOMOD_WARN_LOG = "AUTOMOD_WARN_LOG"

	# === Cleanup ===
	CLEANUP_ENABLED = "CLEANUP_ENABLED"
	CLEANUP_LOG = "CLEANUP_LOG"

	# === Restore Threads ===
	RESTORE_ARCHIVED = "RESTORE_ARCHIVED"

	# === Log Changes ===
	LOG_CHANGES = "LOG_CONFIG_CHANGES"
	CHANGE_LOG_CHANNEL = "CHANGES_LOG"

	# === Threads ===
	PING_ON_THREAD = "PING_ON_THREAD"
	PING_ON_THREAD_ROLE = "PING_ON_THREAD_ROLE"
	PING_ON_THREAD_CHANNEL = "PING_ON_THREAD_CHANNEL"


channels = [
	ConfigMapping.AUTOMOD_LOG,
	ConfigMapping.AUTOMOD_WARN_LOG,
	ConfigMapping.CLEANUP_LOG,
	ConfigMapping.CHANGE_LOG_CHANNEL,
	ConfigMapping.PING_ON_THREAD_CHANNEL
]

toggles = [
	ConfigMapping.CLEANUP_ENABLED,
	ConfigMapping.RESTORE_ARCHIVED,
	ConfigMapping.LOG_CHANGES,
	ConfigMapping.PING_ON_THREAD
]

roles = [
	ConfigMapping.PING_ON_THREAD_ROLE

]

docs = {
	# == automod ==
	ConfigMapping.AUTOMOD_LOG        : "The channel ID where general moderation actions and filter triggers are logged.",
	ConfigMapping.AUTOMOD_WARN_LOG   : "The channel ID specifically for logging user warnings and infraction thresholds.",

	# == cleanup ==
	ConfigMapping.CLEANUP_ENABLED    : "Toggle (True/False) to enable or disable the automatic message cleanup service.",
	ConfigMapping.CLEANUP_LOG        : "The channel ID where summaries of deleted messages and cleanup tasks are sent.",

	# == restore threads ==
	ConfigMapping.RESTORE_ARCHIVED   : "Toggle to automatically unarchive or 'bump' threads when they are closed by inactivity.",

	# == Log Changes ==
	ConfigMapping.LOG_CHANGES        : "Toggle to enable logging whenever a configuration value is modified via commands.",
	ConfigMapping.CHANGE_LOG_CHANNEL : "The channel ID where the audit trail for config updates is maintained.",

	# === Threads ===
	ConfigMapping.PING_ON_THREAD: "Enables or disables an automatic notification to staff members whenever a new message is posted in a thread.",
	ConfigMapping.PING_ON_THREAD_ROLE: "Defines the specific staff role (ID or Name) that should be mentioned to ensure the team is alerted to thread activity.",
	ConfigMapping.PING_ON_THREAD_CHANNEL: "Specifies the dedicated channel where staff receive notifications about new thread activity. Enter a Channel ID to redirect pings away from public view and into a private staff-only logs or alerts channel."

}
