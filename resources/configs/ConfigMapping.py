# Cleanup:
# CLEANUPLEFT
# CLEANUPDAYS
# CLEANUPREGEX (regex goes in extra)
from enum import StrEnum

# Logging
# REGULAR
# ARCHIVE
class ConfigMapping(StrEnum):
	"""This is the mapping for the config keys, this way we can avoid typos and have a single source of truth for the config keys."""

	# == automod ==
	AUTOMOD_LOG = "AUTOMOD_LOG"
	AUTOMOD_WARN_LOG = "AUTOMOD_WARN_LOG"

	# == cleanup ==
	CLEANUP_ENABLED = "CLEANUP_ENABLED"

	# == restore threads ==
	RESTORE_ARCHIVED = "RESTORE_ARCHIVED"

channels = [
	ConfigMapping.AUTOMOD_LOG,
	ConfigMapping.AUTOMOD_WARN_LOG,
]

toggles = [
	ConfigMapping.CLEANUP_ENABLED,
	ConfigMapping.RESTORE_ARCHIVED
]