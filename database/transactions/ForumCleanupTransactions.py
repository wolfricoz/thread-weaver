from sqlalchemy import select

from database.database import ForumCleanup
from database.transactions.DatabaseTransactions import DatabaseTransactions


class ForumCleanupTransactions(DatabaseTransactions) :

	def get(self, channel_id: int, key: str, current_session=None) :
		with self.createsession() as session :
			if current_session :
				session = current_session
			return session.scalar(select(ForumCleanup).where(ForumCleanup.forum_id == channel_id, ForumCleanup.key == key))

	def add(self, channel_id: int, key: str, days: int = None, extra: str = None) :
		with self.createsession() as session :
			if self.get(channel_id, key, session) :
				return self.update(channel_id, key, days, extra)
			cleanup = ForumCleanup(forum_id=channel_id, key=key, days=days, extra=extra)
			session.add(cleanup)
			self.commit(session)
			return cleanup

	def delete(self, channel_id: int, key: str) :
		with self.createsession() as session :
			entity = self.get(channel_id, key, session)

			if not entity :
				return False
			session.delete(entity)
			self.commit(session)
			return True

	def update(self, channel_id: int, key: str, days: int = None, extra: str = None) :
		with self.createsession() as session :
			entity = self.get(channel_id, key, session)
			if not entity :
				return False
			updated = {
				'days': days,
				'extra': extra
			}

			for key, value in updated.items() :
				setattr(entity, key, value)
			self.commit(session)
			return entity


