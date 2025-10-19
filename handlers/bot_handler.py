import aiogram
import asyncio
import json
import services.keyboard.keyboard as kb
import services.db.db_service as db
from random import randint, choice
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings_bot

db_api = db.DataBaseAPI()

bot = Bot(settings_bot.BOT_TOKEN)
dp = Dispatcher()

class AddWordState(StatesGroup):
    waiting_word = State()
    waiting_translate_word = State()

class DellWordState(StatesGroup):
    waiting_word = State()

class Learn(StatesGroup):
    showing_word = State()
    waiting_answer = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id 
    await db_api.add_user(user_id=user_id, chat_id=chat_id)
    await message.answer(text='Привет, выбери, что ты хочешь дальше', reply_markup=kb.start_keyboard)

@dp.message(F.text == '▶️Старт обучения')
async def start_learning(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_words = await db_api.get_id_word(user_id=user_id)
    if not user_words:
        await message.answer("У вас пока нет слов для изучения.")
        return

    await state.update_data(words=user_words, learned=set())
    await show_word(message, state)


async def show_word(message: Message, state: FSMContext):
    data = await state.get_data()
    words = data.get('words')
    learned = data.get('learned', set())

    # Находим следующее слово, не входящее в learned
    remaining_words = [w for w in words if w not in learned]
    if not remaining_words:
        await message.answer("Вы изучили все слова! Поздравляю!")
        await state.clear()
        return

    word_id = remaining_words[0]
    word_obj = await db_api.get_word_by_id(word_id)
    correct_translation = word_obj.translate_word

    options = await db_api.get_random_translations(exclude_word=correct_translation, count=3)
    import random
    buttons = options + [correct_translation]
    random.shuffle(buttons)

    keyboard = await kb.keyboard_word_create(*buttons)
    await message.answer(f"Как переводится слово: {word_obj.word}?", reply_markup=keyboard)

    learned.add(word_id)
    await state.update_data(current_correct=correct_translation, current_word=word_id, learned=learned)
    await state.set_state(Learn.waiting_answer)


@dp.message(Learn.waiting_answer)
async def check_answer(message: Message, state: FSMContext):
    user_answer = message.text.strip()
    data = await state.get_data()
    correct_answer = data.get('current_correct')
    learned = data.get('learned', set())
    words = data.get('words', [])
    user_id = message.from_user.id

    if user_answer == '⏭️Пропустить':
        await show_word(message, state)
        return

    if user_answer == '❌Удалить слово':
        word_id = data.get('current_word')
        word_obj = await db_api.get_word_by_id(word_id)
        await db_api.del_user_word(user_id=user_id, user_word=word_obj.word)
        
        # Обновляем список слов и learned
        updated_words = await db_api.get_id_word(user_id=user_id)
        if not updated_words:
            await message.answer("Вы удалили все слова. Добавьте новые для продолжения.")
            await state.clear()
            return
        # Убираем удалённое слово из learned
        learned.discard(word_id)
        await state.update_data(words=updated_words, learned=learned)
        await message.answer(f"Слово '{word_obj.word}' удалено.")
        await show_word(message, state)
        return

    if user_answer == correct_answer:
        await message.answer("Верно! 🎉")
        await show_word(message, state)
    else:
        await message.answer("Неверно, попробуйте еще раз.")

@dp.message(F.text == '🔢Количество слов для изучения')
async def start_count_word(message: Message):
    len_ = len(await db_api.get_id_word(user_id=message.from_user.id))
    await message.answer(f'{len_}')

@dp.message(F.text == '➕Добавить слово')
async def start_add_word_step_1(message: Message, state: FSMContext):
    await message.reply('Приступим к добавлению. Введите слово на изучаемом языке')
    await state.set_state(AddWordState.waiting_word)

@dp.message(AddWordState.waiting_word)
async def add_word_step_2(message: Message, state: FSMContext):
    word = message.text.strip().lower()
    await state.update_data(word=word)
    await message.reply('Введтие перевод слова')
    await state.set_state(AddWordState.waiting_translate_word)

@dp.message(AddWordState.waiting_translate_word)
async def add_word_step_3(message: Message, state: FSMContext):
    data = await state.get_data()
    word = data.get('word')
    translate = message.text.strip().lower()
    await db_api.add_user_word(user_id=message.from_user.id, user_word=word, translate_word=translate)
    await state.clear()
    await message.reply(f'Слово {word}, перевод {translate} добавлено')

@dp.message(F.text == '❌Удалить слово')
async def start_learn_word(message: Message, state: FSMContext):
    await message.reply('Введите слово которое хотите удалить.')
    await state.set_state(DellWordState.waiting_word)

@dp.message(DellWordState.waiting_word)
async def del_word_step(message: Message, state: FSMContext):
    word = message.text.strip().lower()
    user_id = message.from_user.id
    await db_api.del_user_word(user_id=user_id, user_word=word)
    count_word = await db_api.get_id_word(user_id=user_id)
    await message.reply(f'Слово {word} - удалено.\nТеперь вы изучаете: {len(count_word)} слов')

async def bot_hendler_start():
    await dp.start_polling(bot)