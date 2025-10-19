import asyncio
import json
import random
from database import model_db as mdl
from sqlalchemy import select, delete
from sqlalchemy.orm import aliased
from sqlalchemy.exc import MultipleResultsFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from config import async_engine


class DataBaseAPI():

    __async_sessionmaker = async_sessionmaker(
        async_engine,
        class_= AsyncSession
    )

    # Читаем файл с первичными словами
    async def read_json(self) -> list[dict]:
        file_adress = './data/AllWords.json'
        def _sync_read():
            with open(file_adress, 'r', encoding='utf-8') as file:
                return json.load(file)
        data = await asyncio.to_thread(_sync_read)
        return data

    # Грузим в БД данные о первичных словах
    async def add_data(self, data: list[dict]):
        words = [mdl.GeneralWords(**d) for d in data]
        async with self.__async_sessionmaker() as conn:
            conn.add_all(words)
            await conn.commit()

    # Добавляем юзера, строим взаимосвязи с исходными словами
    async def add_user(self, user_id: int, chat_id: int):
        try:
            add_user = {'user_id': user_id, 'chat_id': chat_id}
            user_obj = mdl.Users(**add_user)
            async with self.__async_sessionmaker() as conn:
                conn.add(user_obj)
                await conn.commit()
                await conn.refresh(user_obj)
                id = user_obj.id
                stmt = select(mdl.GeneralWords.id)
                result_select = await conn.scalars(stmt)
                id_words = result_select.unique().all()
                for id in id_words:
                    user_word = {'user_id': user_obj.id, 'general_word_id': id}
                    add = mdl.WordsUsers(**user_word)
                    conn.add(add)
                await conn.commit()
        except IntegrityError:
            pass

    # Добавляем индивидуальные слова юзера, строим взаимосвязь
    async def add_user_word(self, user_id: int, user_word: str, translate_word: str):
        result_word = {'word': user_word, 'translate_word': translate_word}
        add_word = mdl.UserWords(**result_word)
        async with self.__async_sessionmaker() as conn:
            stmt = (
                select(mdl.GeneralWords)
                .where(mdl.GeneralWords.word == user_word)
            )
            try:
                result = await conn.execute(stmt)
                obj = result.scalars().one_or_none()
                if obj is not None:
                    return "Слово не добавлено - есть в общем списке"
            except MultipleResultsFound:
                return "Слово не добавлено - есть в общей списке"
            conn.add(add_word)
            await conn.commit()
            await conn.refresh(add_word)
            pk_new_word = add_word.id
            stmt = (
                select(mdl.Users.id)
                .where(mdl.Users.user_id == user_id)
            )
            result = await conn.execute(stmt)
            id = result.scalar_one()
            result_add_word_user = {'user_id': id, 'personal_word_id': pk_new_word}
            add_word_user = mdl.WordsUsers(**result_add_word_user)
            conn.add(add_word_user)
            await conn.commit()


    #Дропаем слова
    async def del_user_word(self, user_id: int, user_word: str):
        async with self.__async_sessionmaker() as conn:
            stmt_user_word_id = (
            select(mdl.UserWords.id)
            .join(mdl.WordsUsers, mdl.UserWords.id == mdl.WordsUsers.personal_word_id)
            .join(mdl.Users, mdl.Users.id == mdl.WordsUsers.user_id)
            .where(mdl.Users.user_id == user_id, mdl.UserWords.word == user_word)
        )
            delete_user_words = (
                delete(mdl.UserWords)
                .where(mdl.UserWords.id.in_(stmt_user_word_id))
            )
            await conn.execute(delete_user_words)
            wu = aliased(mdl.WordsUsers)
            stmt_general_word = (
                select(wu.id)
                .join(mdl.Users, mdl.Users.id == wu.user_id)
                .join(mdl.GeneralWords, mdl.GeneralWords.id == wu.general_word_id)
                .where(mdl.Users.user_id == user_id, mdl.GeneralWords.word == user_word)
            )
            del_stmt = (
                delete(mdl.WordsUsers)
                .where(mdl.WordsUsers.id.in_(stmt_general_word))
            )
            await conn.execute(del_stmt)
            await conn.commit()

    #Получаем id слов пользователя
    async def get_id_word(self, user_id: int):
        stmt = (
            select(mdl.WordsUsers.id)
            .join(mdl.WordsUsers.user_word)
            .where(mdl.Users.user_id == user_id)
        )
        async with self.__async_sessionmaker() as conn:
            result = await conn.execute(stmt)
            id_relations = result.scalars().all()
        return id_relations
    
    async def get_word_by_id(self, word_id: int):
        async with self.__async_sessionmaker() as conn:
            stmt = select(mdl.GeneralWords).where(mdl.GeneralWords.id == word_id)
            result = await conn.execute(stmt)
            return result.scalars().one_or_none()

    async def get_random_translations(self, exclude_word: str, count: int = 3):
        async with self.__async_sessionmaker() as conn:
            stmt = select(mdl.GeneralWords.translate_word).where(mdl.GeneralWords.translate_word != exclude_word)
            result = await conn.execute(stmt)
            translations = result.scalars().all()
            return random.sample(translations, min(count, len(translations)))