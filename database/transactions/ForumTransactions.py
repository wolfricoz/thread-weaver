from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from database.database import ForumPatterns, Forums
from database.transactions.DatabaseTransactions import DatabaseTransactions
from database.transactions.ServerTransactions import ServerTransactions
from data.enums.PatternTypes import ForumPatterns as FP

class ForumTransactions(DatabaseTransactions):

	def add(self, channel_id, server_id, name) -> Forums | None :
		if not ServerTransactions().exists(server_id) :
			ServerTransactions().add(guild_id=server_id, owner="unknown", name="unknown", member_count=0, invite="unknown")
		with self.createsession() as session:
			if self.get(channel_id):
				self.update(channel_id, name)
				return self.get(channel_id)
			forum = Forums(
				id=channel_id,
				server_id=server_id,
				name=name
			)
			session.add(forum)
			self.commit(session)
			return forum

	def update(self, channel_id: int, name: str = None, minimum_characters: int = None, duplicates:bool = None) -> Forums | None :
		with self.createsession() as session:
			forum = self.get(channel_id)
			if forum is None :
				return None
			available_fields = {
				"name": name,
				"minimum_characters": minimum_characters,
				"duplicates": duplicates
			}
			for key, value in available_fields.items():
				if value is not None:
					setattr(forum, key, value)
			session.add(forum)
			self.commit(session)
			return forum

	def delete(self, channel_id: int) -> None :
		with self.createsession() as session:
			forum = self.get(channel_id, current_session=session)
			if forum is None :
				return
			session.delete(forum)
			self.commit(session)

	def get(self, channel_id, current_session = None) -> Forums | None :
		with self.createsession() as session:
			if current_session :
				session = current_session
			return session.scalar(select(Forums).outerjoin(ForumPatterns).options(joinedload(Forums.patterns)).where(Forums.id == channel_id))

	def get_all(self, server_id, id_only = False) -> list[Forums] :
		with self.createsession() as session:
			if id_only :
				return session.scalars(select(Forums.id).where(Forums.server_id == server_id)).all()
			return session.scalars(select(Forums).where(Forums.server_id == server_id)).all()

	# === Patterns === #
	# Patterns are added here, because they are directly linked to forums. A separate transaction class would be overkill.


	def add_pattern(self, channel_id: int, name: str, pattern: str, action: str = "BLOCK") -> ForumPatterns | None :
		with self.createsession() as session:
			forum = self.get(channel_id)
			if forum is None :
				return None
			p = ForumPatterns(
				name=name,
				forum_id=forum.id,
				pattern=pattern,
				action=action.upper()
			)
			session.add(p)
			self.commit(session)
			return p

	def remove_pattern(self, pattern_id: int) -> bool :
		with self.createsession() as session:
			pattern = session.get(ForumPatterns, pattern_id)
			if pattern is None :
				return False
			session.delete(pattern)
			self.commit(session)
			return True

	def get_pattern(self, channel_id: int, name: str) -> ForumPatterns | None :
		with self.createsession() as session:
			return session.scalar(select(ForumPatterns).where(ForumPatterns.forum_id == channel_id, ForumPatterns.name == name))

	def get_patterns_by_type(self, channel_id: int, pattern_type: str) -> list[ForumPatterns] :
		with self.createsession() as session:
			return session.scalars(select(ForumPatterns).where(ForumPatterns.forum_id == channel_id, ForumPatterns.action == pattern_type)).all()

	def get_all_patterns(self, channel_id: int, exclude_blacklist = False) -> list[ForumPatterns] :
		with self.createsession() as session:
			if exclude_blacklist:
				return session.scalars(select(ForumPatterns).where(ForumPatterns.forum_id == channel_id, ForumPatterns.action != FP.blacklist)).all()
			return session.scalars(select(ForumPatterns).where(ForumPatterns.forum_id == channel_id)).all()

	def count_patterns(self, channel_id: int) -> int :
		with self.createsession() as session:
			return session.scalar(text("SELECT COUNT(*) FROM forum_patterns WHERE forum_id = :channel_id"),  {"channel_id": channel_id})
