from aiogram import Router, F, html
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
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
load_dotenv()
router = Router()
import test_tg_bot.app.keyboards as kb
from db import get_game, update_game
from aiogram.filters import callback_data
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
class Enrolling(StatesGroup):
    enrolling = State()
@router.message(CommandStart(deep_link=True, magic=F.args.contains("enter_")))
async def enroll(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    game_id = int(command.args.split("_")[1])
    game_data = await get_game(game_id, session)
    game_data = game_data[0]
    print(type(game_data.game_data))
    game_data = json.loads(game_data.game_data)
    await message.answer(
        'Приветствую вас, отважные искатели приключений!\n'
        'Да начнётся игра!\n'
        f'Жанр:{game_data['genre']}\n'
        f'Цель игры:{game_data['purpose']}\n'
        f'Сложность: {game_data['complexity']}'
    )
    enroll_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Присоединиться!', callback_data=f'enroll_{game_id}')]
        ]
    )
    await state.set_state(Enrolling.enrolling)
    await state.update_data({"enrolling": [], "game_id": game_id})
    await message.answer(
        'Ведётся набор игроков:',
        reply_markup=enroll_kb
    )
'''@router.message(
    Command('char_sender'),
    F.chat.type.in_({'group', 'supergroup'}),
    F.text.regexp(r'^/char_sender@truedndbot') or F.text.regexp(r'/char_sender\b')
)'''
@router.callback_query(F.data.contains('enroll_'),Enrolling.enrolling)
async def enrolling_person(callback:CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enrolling_guys = data['enrolling']
    if [callback.from_user.full_name, callback.from_user.username] not in enrolling_guys:
        enrolling_guys.append([callback.from_user.full_name, callback.from_user.username, callback.from_user.id])
    await callback.answer()
    ans = ''
    for el in enrolling_guys:
        ans = ans+f'{html.link(el[0], "https://t.me/"+el[1])}, ID:{el[2]}\n'
    enroll_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Присоединиться!', callback_data=f'enroll_{data['game_id']}')]
        ]
    )
    try:
        await callback.message.edit_text(
            'Ведётся набор игроков\n'
            'Играют:\n'
            f'{ans}\n\n'
            f'Чтобы присоединиться к игре, нажми кнопку ниже\n'
            'Чтобы запустить игру,'
            'отправь комманду /sg@truedndbot',
            parse_mode='HTML',
            reply_markup=enroll_kb
        )
    except:
        pass
    await state.update_data(enrolling=enrolling_guys)
@router.message(Command('sg'),
                       F.chat.type.in_({'group', 'supergroup'}),
                       F.text.regexp(r'^/sg@truedndbot') or F.text.regexp(r'/start\b'),
                       Enrolling.enrolling)
async def enrolled(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    print('here')
    game_id = data['game_id']
    game_data = await get_game(game_id, session)
    game_data = game_data[0]
    game_data = game_data.game_data
    game_data = json.loads(game_data)
    print(game_data)
    game_data['players_count'] = len(data['enrolling'])
    await update_game(game_id, {"game_data":json.dumps(game_data)}, session)
    launch_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Создать персонажа!',
                                  url="https://t.me/truedndbot?start=char_" + str(game_id) + "_" + str(
                                      message.chat.id))],
            [InlineKeyboardButton(text='Запуск!', callback_data=f'launch_{data['game_id']}')],
        ]
    )
    await message.answer('Отлично! Теперь каждый игрок должен '
                         f'создать персонажа, нажав кнопку "Создать персонажа!" ниже.\n Когда все создадут персонажей, '
                         f'Нажми кнопку "Запуск!" ниже',
                         parse_mode='HTML', reply_markup=launch_kb)

    await state.clear()
