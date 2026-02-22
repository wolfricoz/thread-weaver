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

channels = [
	ConfigMapping.AUTOMOD_LOG
]
