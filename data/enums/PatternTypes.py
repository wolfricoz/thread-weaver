from enum import StrEnum


class ForumPatterns (StrEnum) :
	blacklist = "BLACKLIST" # does the same as block, but this isn't a pattern - just a flat word check
	block = "BLOCK" # This is the pattern version of blacklist; this is actually a pattern, so you can use regex here. This will block the post if the pattern is found.
	warn = "WARN" # this will warn the user if the pattern is found, but it won't block the post. This is useful for patterns that you want to monitor but not necessarily block.
	required = "REQUIRED" # this will require the pattern to be present in the post. If the pattern is not found, the post will be blocked. This is useful for patterns that you want to enforce in your forum channels, such as a specific format for posts or a required hashtag.

