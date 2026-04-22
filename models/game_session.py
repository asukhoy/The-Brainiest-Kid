import enum

from sqlalchemy import Integer, String, UUID, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from db import Base

from .game_mode import GameMode

class GameSession(Base):
    __tablename__ = 'sessions'

    session_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_data: Mapped[str] = mapped_column(String, nullable=False)

    current_round: Mapped[int] = mapped_column(Integer, default=1)
    current_mode: Mapped[GameMode] = mapped_column(Enum(GameMode), default=GameMode.DEFAULT)

    secret: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4)

    player = relationship('Player', back_populates='session')
    question = relationship('Question', back_populates='session')

    def to_dict(self):
        return {
            'session_code': self.session_code,
            'game_data': self.game_data,
            'current_round': self.current_round,
            'current_mode': self.current_mode,
            'secret': self.secret
        }