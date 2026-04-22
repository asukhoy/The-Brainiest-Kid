from sqlalchemy import UUID, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from db import Base

class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    session_code: Mapped[int] = mapped_column(Integer,
                                              ForeignKey('sessions.session_code', ondelete="CASCADE"),
                                              nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[int] = mapped_column(Integer, default=0)

    session = relationship('GameSession', back_populates='question')

    def to_dict(self):
        return {
            'id': str(self.id),
            'session_code': self.session_code,
            'round_number': self.round,
            'question': self.question
        }