# Cleanup:
# CLEANUPLEFT
# CLEANUPDAYS
# CLEANUPREGEX (regex goes in extra)
from enum import StrEnum

class ConfigMapping(StrEnum):
	"""This is the mapping for the config keys, this way we can avoid typos and have a single source of truth for the config keys."""

	# == automod ==
	AUTOMOD_LOG = "AUTOMOD_LOG"
	AUTOMOD_WARN_LOG = "AUTOMOD_WARN_LOG"

	# == cleanup ==
	CLEANUP_ENABLED = "CLEANUP_ENABLED"
	CLEANUP_LOG = "CLEANUP_LOG"

	# == restore threads ==
	RESTORE_ARCHIVED = "RESTORE_ARCHIVED"

	# == Log Changes ==
	LOG_CHANGES = "LOG_CONFIG_CHANGES"
	CHANGE_LOG_CHANNEL = "CHANGES_LOG"

channels = [
	ConfigMapping.AUTOMOD_LOG,
	ConfigMapping.AUTOMOD_WARN_LOG,
	ConfigMapping.CLEANUP_LOG,
	ConfigMapping.CHANGE_LOG_CHANNEL
]

toggles = [
	ConfigMapping.CLEANUP_ENABLED,
	ConfigMapping.RESTORE_ARCHIVED,
	ConfigMapping.LOG_CHANGES
]




docs = {
    # == automod ==
    ConfigMapping.AUTOMOD_LOG: "The channel ID where general moderation actions and filter triggers are logged.",
    ConfigMapping.AUTOMOD_WARN_LOG: "The channel ID specifically for logging user warnings and infraction thresholds.",

    # == cleanup ==
    ConfigMapping.CLEANUP_ENABLED: "Toggle (True/False) to enable or disable the automatic message cleanup service.",
    ConfigMapping.CLEANUP_LOG: "The channel ID where summaries of deleted messages and cleanup tasks are sent.",

    # == restore threads ==
    ConfigMapping.RESTORE_ARCHIVED: "Toggle to automatically unarchive or 'bump' threads when they are closed by inactivity.",

    # == Log Changes ==
    ConfigMapping.LOG_CHANGES: "Toggle to enable logging whenever a configuration value is modified via commands.",
    ConfigMapping.CHANGE_LOG_CHANNEL: "The channel ID where the audit trail for config updates is maintained."
}