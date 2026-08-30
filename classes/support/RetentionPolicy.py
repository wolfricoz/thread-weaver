import logging

from database.transactions.ServerTransactions import ServerTransactions

# How long a soft-deleted server is kept before its row is removed for good.
# Stated as 30 days in the privacy policy; change both together.
RETENTION_DAYS = 30


def enforce_data_retention_policy() :
	"""Removes data we no longer have a reason to hold.

	The only Discord-provided personal data we store is the guild owner's id and
	name on the servers table. While the bot is in a guild that is operational
	data; once it has been removed there is no longer a reason to keep it, so the
	row and everything cascading from it is deleted after the retention window.
	"""
	removed = ServerTransactions().purge_expired(RETENTION_DAYS)
	logging.info(f"Retention: permanently removed {removed} servers soft-deleted over {RETENTION_DAYS} days ago")
	return removed
