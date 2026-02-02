from sqlalchemy import UUID, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from db import Base


class Player(Base):
    __tablename__ = 'players'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    session_id: Mapped[int] = mapped_column(Integer,
                                              ForeignKey('sessions.id'),
                                              nullable=False)
    name: Mapped[String] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_host: Mapped[bool] = mapped_column(Boolean, default=False)

    session = relationship('GameSession', back_populates='player')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'name': self.name,
            'score': self.score,
            'is_connected': self.is_connected,
            'is_host': self.is_host
        }