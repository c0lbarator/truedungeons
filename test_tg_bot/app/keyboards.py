from aiogram.filters import callback_data
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛠️ Создать игру', callback_data='generate_game')],
    [InlineKeyboardButton(text='👤 Пользователь', callback_data='lk'),
     InlineKeyboardButton(text='❓ Помощь', callback_data='help')]]
)

menu_generate_numbers = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=str(i)) for i in range(2, 6)],
    [KeyboardButton(text=str(i)) for i in range(6, 11)]],
    resize_keyboard=True)

menu_generate_genre = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Политический/Социальный'), KeyboardButton(text='Эпическое/Героическое')],
    [KeyboardButton(text='Драматический/Персонажный'), KeyboardButton(text='Мистический/Ужас')],
    [KeyboardButton(text='Фэнтези'), KeyboardButton(text='Приключенческий'), KeyboardButton(text='Миротворческий')]],
    resize_keyboard=True, one_time_keyboard=True)

menu_generate_purpose = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Легкий'), KeyboardButton(text='Средний'), KeyboardButton(text='Сложный')]],
    resize_keyboard=True, one_time_keyboard=True)


menu_lk = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏪ Назад', callback_data='start')]
])

menu_help = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='<клик>', url="https://teletype.in/@retrobich921/N1oy7GOnpku")],
    [InlineKeyboardButton(text='⏪ Назад', callback_data='start')]
])

settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="YouTube", url="https://www.youtube.com/watch?v=dQw4w9WQg")]
])

help = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='<клик>', url="")]
])

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да!\nЯ готов⚡️', callback_data='start')]
])

cars = ["Tesla", 'Mercedes', 'BMW', 'Volkswagen']


async def inline_cars():
    keyboard = InlineKeyboardBuilder()
    for car in cars:
        keyboard.add(InlineKeyboardButton(text=car, url="https://www.youtube.com/watch?v=dQw4w9WQg"))
    return keyboard.adjust(3).as_markup()
