from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def keyboard_word_create(*args):
    w1, w2, w3, w4 = args
    repl_key_mark = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text= f'{w1}'), KeyboardButton(text=f'{w2}')],
        [KeyboardButton(text= f'{w3}'), KeyboardButton(text= f'{w4}')],
        [KeyboardButton(text='❌Удалить слово (это прервет обучение)'), KeyboardButton(text='⏭️Пропустить')],
        [KeyboardButton(text='➕Добавить слово (это прервет обучение)')]
        ],
        resize_keyboard=True)
    return repl_key_mark

start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='▶️Старт обучения'), KeyboardButton(text='🔢Количество слов для изучения')],
    [KeyboardButton(text='❌Удалить слово'), KeyboardButton(text='➕Добавить слово')]
    ],
    resize_keyboard=True)