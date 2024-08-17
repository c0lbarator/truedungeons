from aiogram import Router, F, html
from aiogram.filters import Command, CommandStart, CommandObject
from filters.chat_type import ChatTypeFilter
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions
from groq import AsyncGroq, DefaultAsyncHttpxClient
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import json
import os
from db import create_game
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncClient

import test_tg_bot.app.keyboards as kb
from db import get_game
from aiogram.filters import callback_data
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from prompts import target_creation
load_dotenv()
router = Router()
class Reg_session(StatesGroup):
    #number_of_players = State()  # количество игроков
    genre = State()  # жанр игры
    purpose = State()  # цель
    complexity = State()  # сложность (легкая, средняя, сложная)

@router.message(CommandStart(deep_link=False), ChatTypeFilter(chat_type=['private']))
async def cmd_start(message: Message):
    await message.answer(
        'Приветствую тебя, отважный искатель приключений!\nРешил поиграть в DnD с друзьями? 🎲\n\nЯ — твой верный помощник и ведущий в увлекательном мире Dungeons & Dragons. Вместе мы погрузимся в незабываемые приключения, где твои решения определят судьбу героев и исход великих сражений. \n\nНажимай на кнопки, задавай вопросы и готовься к неожиданным поворотам сюжета. Я помогу тебе создать захватывающий мир, в котором оживут твои самые смелые фантазии. Готов к началу путешествия?\n\nВ путь, герой! 🗡️✨',
        reply_markup=kb.start)


@router.callback_query(F.data == 'start')
async def menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Прекрасно! Добро пожаловать в меню организатора игры.'
                                     ' Выбирай, что ты хочешь сделать:',
                                     reply_markup=kb.menu)

@router.callback_query(F.data == 'generate_game')
async def menu_generate_numder(callback: CallbackQuery, state: FSMContext):
    #await state.update_data(number_of_players=int(message.text))
    await callback.message.answer(text='Давай настроим параметры игры. Вначале выберем жанр\n'
                              'О жанрах можешь почитать здесь /genre',
                         reply_markup=kb.menu_generate_genre)
    await state.set_state(Reg_session.genre)


@router.message(Reg_session.genre, F.text.in_(['Политический/Социальный', 'Эпическое/Героическое', 'Драматический/Персонажный', 'Мистический/Ужас', 'Фэнтези', 'Приключенческий', 'Миротворческий']))
async def menu_generate_numder(message: Message, state: FSMContext, groq_client: (AsyncGroq if os.getenv('USE_OPENAI') == "False" else AsyncClient)):
    #await state.update_data(genre=str(message.text))
    await message.answer(text='Хм, хм, хм\n'
                              'Теперь следует определиться с целью вашей игры\n'
                              'Вызываю помощника...')
    data = await state.get_data()
    data['game_data'] = {'GAME_STATE': {'genre': str(message.text)}}
    chat_completion = await groq_client.with_options(max_retries=7).chat.completions.create(
        messages=[
            target_creation(data),
            {
                'role': 'user',
                'content': 'Игроки хотят выбрать цель игры'
            }
        ],
        response_format={'type': 'json_object'},
        model=os.getenv("MODEL")
    )
    ans = chat_completion.choices[0].message.content
    ans = json.loads(ans)
    await state.update_data(ans)
    try:
        await message.answer(ans['message'])
    except:
        await message.answer("Упс! Отправь сообщение ещё раз")
    await state.set_state(Reg_session.purpose)



@router.message(Reg_session.purpose)
async def menu_generate_numder(message: Message, state: FSMContext, groq_client: (AsyncGroq if os.getenv('USE_OPENAI') == "False" else AsyncClient)):
    data = await state.get_data()
    if data['target_created'] == "False":
        chat_completion = await groq_client.with_options(max_retries=3).chat.completions.create(
            messages=[
                target_creation(data),
                {
                    'role': 'user',
                    'content': message.text
                }
            ],
            response_format={'type': 'json_object'},
            model=os.getenv("MODEL")
        )
        ans = chat_completion.choices[0].message.content
        ans = json.loads(ans)
        try:
            await message.answer(ans['message'])
            await state.update_data(ans)
            if ans['target_created'] == "True":
                await message.answer(text='Отлично!\n'
                                          'Что по сложности выберем? Если ты новичок, то лучше выбрать полегче)',
                                     reply_markup=kb.menu_generate_purpose)
                await state.set_data(ans)
                await state.set_state(Reg_session.complexity)
        except Exception as e:
            print("Ошибка!", type(e).__name__)
            await message.answer("Упс! Пожалуйста, отправь сообщение ещё раз")


@router.message(F.data == 'generate_game' and Reg_session.complexity)
async def menu_generate_numder(message: Message, state: FSMContext, session: AsyncSession):
    game_data = await state.get_data()
    game_data['GAME_STATE']['complexity'] = message.text
    game_id = await create_game({"game_data": json.dumps(game_data['GAME_STATE'])}, session)
    await message.answer(text='Отлично, игра создана!'
                              'Для запуска игры выбери группу:'
                              f' {html.link("ТЫК", "https://t.me/truedndbot?startgroup="+"enter_"+str(game_id))}', parse_mode='HTML')
    await state.clear()


@router.callback_query(F.data == 'lk')
async def menu_lk(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        f'➖➖➖➖➖➖➖➖➖➖➖\n   ℹ️ Информация о вас: @{callback.from_user.username}\n   💳 ID: {callback.from_user.id}\n\n   🕹 Сыграно игр: {data_user.get(callback.from_user.id, 'Нет данных :/\n➖➖➖➖➖➖➖➖➖➖➖')}',
        reply_markup=kb.menu_lk)


@router.callback_query(F.data == 'help')
async def menu_help(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        'Помощь приветствует тебя, но она не скорая 😥\nНажав на кнопку снизу, сможешь познакомиться с правилами игры :)',
        reply_markup=kb.menu_help)


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('👇🏻Правила игры можно посмотреть вот тут👇🏻',
                         reply_markup=kb.help)


@router.message(Command('genre'))
async def cmd_help(message: Message):
    await message.answer('Всё о жанрах, можешь почитать здесь 🎭\n\n'
                         '<i>1)</i>  <b>Фэнтези:</b>  Это основной жанр D&D. Игроки обычно исследуют волшебные миры, сталкиваются с драконами, магическими существами и древними проклятиями. Основные сеттинги, такие как Forgotten Realms или Greyhawk, принадлежат к этому жанру.\n\n'
                         '<i>2)</i>  <b>Приключенческий:</b>  В этом жанре акцент сделан на приключениях и исследованиях. Игроки могут искать сокровища, разгадать древние загадки и бороться с монстрами. Здесь часто используются сюжетные линии, связанные с поиском артефактов или спасением мира.\n\n'
                         '<i>3)</i>  <b>Мистический/Ужас:</b>  В некоторых кампаниях акцент смещается в сторону мистики и ужаса. Это может включать в себя элементы хоррора, такие как вампиры, призраки и другие сверхъестественные существа. Часто такие игры содержат мрачные и загадочные сюжеты.\n\n'
                         '<i>4)</i>  <b>Политический/Социальный:</b>  Этот жанр фокусируется на взаимодействиях между персонажами и политическими структурами. Игроки могут заниматься дипломатией, манипуляциями и интригами, а также разгадывать сложные социальные и политические ситуации.\n\n', parse_mode='HTML')
    await message.answer(
        '<i>5)</i>  <b>Эпическое/Героическое:</b>  Здесь акцент делается на великих деяниях и героических подвигах. Игроки могут стать участниками великих сражений, бороться с могущественными врагами и достигать эпических целей.\n\n'
        '<i>6)</i>  <b>Драматический/Персонажный:</b>  В этом жанре основной фокус сосредоточен на развитии персонажей и их личных историях. Это может включать в себя сложные внутренние конфликты, эмоциональные драмы и личные испытания.\n\n'
        '<i>7)</i>  <b>Миротворческий:</b>  Иногда игроки погружаются в создание и развитие мира, в котором происходит действие кампании. Это может включать в себя детальную проработку культур, истории и географии.', parse_mode="HTML")
