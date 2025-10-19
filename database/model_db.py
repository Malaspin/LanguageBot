from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy import Integer, String, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import Annotated, Optional

pkint = Annotated[int, mapped_column(primary_key=True)]
var_255 = String(255)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class GeneralWords(Base):
    __tablename__ = 'general_words'
    id: Mapped[pkint]
    word: Mapped[str] = mapped_column(var_255, unique=True, nullable=False)
    translate_word: Mapped[str] = mapped_column(var_255, unique=True, nullable=False)
    general_word: Mapped[bool] = mapped_column(Boolean, unique=False, nullable=True)
    gen_word_user_list: Mapped[list['WordsUsers']] = relationship('WordsUsers', back_populates='gen_word_user')#3

class UserWords(Base):
    __tablename__ = 'user_words'
    id: Mapped[pkint]
    word: Mapped[str] = mapped_column(var_255, unique=False, nullable=False)
    translate_word: Mapped[str] = mapped_column(var_255, unique=False, nullable=False)    
    pers_word_user_list: Mapped[list['WordsUsers']] = relationship('WordsUsers', back_populates='pers_word_user')#1

class Users(Base):
    __tablename__ = 'users'
    id: Mapped[pkint]
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    user_word_list: Mapped[list['WordsUsers']] = relationship('WordsUsers', back_populates='user_word')#2

class WordsUsers(Base):
    __tablename__ = 'words_users'
    id: Mapped[pkint]
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    general_word_id: Mapped[int] = mapped_column(Integer, ForeignKey('general_words.id', ondelete='CASCADE'), nullable=True)
    personal_word_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_words.id', ondelete='CASCADE'), nullable=True)
    user_word: Mapped[Users] = relationship('Users', back_populates='user_word_list')#2
    pers_word_user: Mapped[UserWords] = relationship('UserWords', back_populates='pers_word_user_list')#1
    gen_word_user: Mapped[GeneralWords] = relationship('GeneralWords', back_populates='gen_word_user_list')#3


    __table_args__ = (
        CheckConstraint(
            """
            (general_word_id IS NOT NULL AND personal_word_id IS NULL) OR 
            (general_word_id IS NULL AND personal_word_id IS NOT NULL)
            """,
            name = 'check_uniq_line'
        ),
    )
    
    @validates('general_word_id', 'personal_word_id')
    def validate_uniq_line(self, key: str, value: Optional[int]):
        if key == 'general_word_id' and value is not None and self.personal_word_id is not None:
            raise ValueError ('В записи должен быть заполнен либо атрибут "general_word_id", либо "personal_word_id"')
        if key == 'personal_word_id' and value is not None and self.general_word_id is not None:
            raise ValueError ('В записи должен быть заполнен либо атрибут "general_word_id", либо "personal_word_id"')
        return value