from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import random

from db import Base



class GameSession(Base):
    __tablename__ = 'sessions'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String, nullable=False)

    current_round: Mapped[int] = mapped_column(Integer, default=1)
    current_question: Mapped[int] = mapped_column(Integer, default=1)

    player = relationship('Player', back_populates='session')

    def to_dict(self):
        return {
            'code': self.code,
            'path': self.path,
            'current_round': self.current_round,
            'current_question': self.current_question
        }