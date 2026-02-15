import re

from resources.configs.Limits import REGEX_MAX_LIMIT, REGEX_MIN_LIMIT


def verify_regex_length(pattern):
	if REGEX_MIN_LIMIT < len(pattern) > REGEX_MAX_LIMIT:
		return False
	return True


def verify_regex_pattern(pattern: str):
	try :
		return re.compile(pattern)

	except re.error :
		return False
