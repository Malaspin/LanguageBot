from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import Annotated

pkint = Annotated[int, mapped_column(primary_key=True)]
var_255 = String(255)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class GeneralWords(Base):
    __tablename__ = 'general_words'
    id: Mapped[pkint]
    word: Mapped[str] = mapped_column(var_255, unique=True, nullable=False)
    translate_word: Mapped[str] = mapped_column(var_255, unique=True, nullable=False)
    word_blackhole_list: Mapped[list['UserBlackHole']] = relationship('UserBlackHole', back_populates='word_blackhole')

class UserWords(Base):
    __tablename__ = 'user_words'
    id: Mapped[pkint]
    word: Mapped[str] = mapped_column(var_255, unique=False, nullable=False)
    translate_word: Mapped[str] = mapped_column(var_255, unique=False, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user: Mapped['Users'] = relationship('Users', back_populates='personal_words')

    __table_args__ = (
        UniqueConstraint('word', 'user_id', name='uniq_word_user'),
    )

class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personal_words: Mapped[list['UserWords']] = relationship('UserWords', back_populates='user')
    user_blackhole_list: Mapped[list['UserBlackHole']] = relationship('UserBlackHole', back_populates='user_blackhole')

class UserBlackHole(Base):
    __tablename__ = 'blackhole_word'
    id: Mapped[pkint]
    id_general_word: Mapped[int] = mapped_column(Integer, ForeignKey('general_words.id'))
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey('users.id', ondelete='CASCADE'))
    word_blackhole: Mapped['GeneralWords'] = relationship('GeneralWords', back_populates='word_blackhole_list')
    user_blackhole: Mapped['Users'] = relationship('Users', back_populates='user_blackhole_list')
