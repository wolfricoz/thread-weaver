import unittest

from database.database import create_bot_database, drop_bot_database
from database.transactions.ForumTransactions import ForumTransactions


class TestForumTransactions(unittest.TestCase) :
	forumclass = ForumTransactions()
	guild_id = 123456789012345678
	user_id = 987654321098765432
	channel_id = 192837465564738291

	def setUp(self) :
		create_bot_database()

	def tearDown(self) :
		drop_bot_database()

	def test_add_forum(self) :
		self.forumclass.add(
			channel_id=self.channel_id,
			server_id=self.guild_id,
			name="Test Forum Channel",
		)
		forum = self.forumclass.get(self.channel_id)

		self.assertEqual("Test Forum Channel", forum.name)
		self.assertEqual(self.guild_id, forum.server_id)
		self.assertEqual(self.channel_id, forum.id)

	def test_get_all_forums(self) :
		channel3 = 564738291192837465

		self.forumclass.add(
			channel_id=self.channel_id,
			server_id=self.guild_id,
			name="Test Forum Channel",
		)
		forums = self.forumclass.get_all(self.guild_id)

		self.assertEqual(1, len(forums))
		self.assertEqual("Test Forum Channel", forums[0].name)
		self.forumclass.add(
			channel_id=self.channel_id,
			server_id=self.guild_id,
			name="Test Forum Channel 2",
		)
		self.forumclass.add(
			channel_id=channel3,
			server_id=self.guild_id,
			name="Test Forum Channel 3",
		)

		forums = self.forumclass.get_all(self.guild_id)
		self.assertEqual(2, len(forums))
		names = [forum.name for forum in forums]
		self.assertIn("Test Forum Channel 2", names)
		self.assertIn("Test Forum Channel 3", names)

	def test_add_forum_pattern(self) :
		pattern = ".*help.*"
		self.forumclass.add(
			channel_id=self.channel_id,
			server_id=self.guild_id,
			name="Test Forum Channel"
		)

		self.forumclass.add_pattern(
			channel_id=self.channel_id,
			name="Help patterm",
			pattern=pattern,
		)
		forum = self.forumclass.get(self.channel_id)

		self.assertEqual(pattern, forum.patterns[0].pattern)
		self.assertEqual(1, len(forum.patterns))
