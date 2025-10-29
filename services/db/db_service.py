import asyncio
import json
import random
from database import model_db as mdl
from sqlalchemy import select, delete, and_
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
    async def add_user(self, user_id: int):
        try:
            add_user = {'id': user_id}
            user_obj = mdl.Users(**add_user)
            async with self.__async_sessionmaker() as conn:
                conn.add(user_obj)
                await conn.commit()
        except IntegrityError:
            pass

    # Добавляем индивидуальные слова юзера
    async def add_user_word(self, user_id: int, user_word: str, translate_word: str):
        result_word = {'word': user_word, 'translate_word': translate_word, 'user_id': user_id}
        async with self.__async_sessionmaker() as conn:
            stmt = (
                select(mdl.GeneralWords)
                .where((mdl.GeneralWords.word == user_word) & (mdl.GeneralWords.translate_word == translate_word))
            )
            stmt_blackhole = (
                select(mdl.UserBlackHole.id)
                .join(mdl.GeneralWords, mdl.GeneralWords.id == mdl.UserBlackHole.id_general_word)
                .where(
                    (mdl.GeneralWords.word == user_word) & 
                    (mdl.UserBlackHole.user_id == user_id) &
                    (mdl.GeneralWords.translate_word == translate_word)
                    )
            )
            stmt_del_blackhole = (
                delete(mdl.UserBlackHole)
                .where(mdl.UserBlackHole.id.in_(stmt_blackhole))
            )
            try:
                balchole_result = await conn.execute(stmt_blackhole)
                id_blackhole = balchole_result.scalars().all()
                if id_blackhole:
                            await conn.execute(stmt_del_blackhole)
                            await conn.commit()
                result = await conn.execute(stmt)
                obj = result.scalars().all()
                if obj:
                    return "Слово не добавлено - есть в общем списке"
                else:  
                    add_word = mdl.UserWords(**result_word)
                try:
                    conn.add(add_word)
                    await conn.commit()
                except IntegrityError:
                    return 'Слово не добавлено - есть в списке персональных слов'
            except MultipleResultsFound:
                return "Слово не добавлено - есть в общей списке"


    #Дропаем слова/общие добавляем в блеклист
    async def del_user_word(self, user_id: int, user_word: str):
        async with self.__async_sessionmaker() as conn:
            stmt_user_word_id = (
            select(mdl.UserWords.id)
            .join(mdl.Users, mdl.Users.id == mdl.UserWords.user_id)
            .where((mdl.Users.id == user_id) & (mdl.UserWords.word == user_word))
        )
            delete_user_words = (
                delete(mdl.UserWords)
                .where(mdl.UserWords.id.in_(stmt_user_word_id))
            )
            stmt_id_general_word = (
                select(mdl.GeneralWords.id)
                .where(mdl.GeneralWords.word == user_word)
            )
            
            find_user_word = await conn.execute(stmt_user_word_id)
            user_word_id = find_user_word.scalars().all()
            if user_word_id:
                await conn.execute(delete_user_words)
                await conn.commit()

            result = await conn.execute(stmt_id_general_word)
            id_general_word = result.scalar_one_or_none()
            if id_general_word:
                try:
                    result_add_blackhole = {'id_general_word':id_general_word, 'user_id': user_id}
                    add_blackhole = mdl.UserBlackHole(**result_add_blackhole)
                    conn.add(add_blackhole)
                except IntegrityError:
                    pass
                await conn.commit()

    #Получаем слова пользователя
    async def get_word(self, user_id: int) -> dict:
        stmt_general = (
            select(mdl.GeneralWords.word, mdl.GeneralWords.translate_word)
            .outerjoin(
                mdl.UserBlackHole,
                and_(
                    mdl.UserBlackHole.id_general_word == mdl.GeneralWords.id,
                    mdl.UserBlackHole.user_id == user_id
                )
            )
            .where(mdl.UserBlackHole.id_general_word.is_(None))
        )
        stmt_personal = (
            select(mdl.UserWords.word, mdl.UserWords.translate_word)
            .where(mdl.UserWords.user_id == user_id)
        )
        async with self.__async_sessionmaker() as conn:
           result_general = await conn.execute(stmt_general)
           word_list = result_general.all()
           result_personal = await conn.execute(stmt_personal)
           word_list += result_personal.all()
           word_dict = dict(word_list)
        return word_dict

    async def get_random_translations(self, exclude_word: str, count: int = 3):
        async with self.__async_sessionmaker() as conn:
            stmt = (
                select(mdl.GeneralWords.translate_word)
                .where(mdl.GeneralWords.translate_word != exclude_word)
                )
            result = await conn.execute(stmt)
            translations = result.scalars().all()
            return random.sample(translations, min(count, len(translations)))