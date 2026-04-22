from sqlalchemy import UUID, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from db import Base
from .player_state import PlayerState

class Player(Base):
    __tablename__ = 'players'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    session_code: Mapped[int] = mapped_column(Integer,
                                              ForeignKey('sessions.session_code', ondelete="CASCADE"),
                                              nullable=False)
    name: Mapped[String] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[PlayerState] = mapped_column(Enum(PlayerState), default=PlayerState.PENDING)
    turn: Mapped[int] = mapped_column(Integer, default=0)

    session = relationship('GameSession', back_populates='player')

    def to_dict(self):
        return {
            'id': str(self.id),
            'session_code': self.session_code,
            'name': self.name,
            'score': self.score,
            'state': self.state.value,
            'turn': self.turn
        }