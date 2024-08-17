from aiogram import Router, F, html
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from groq import AsyncGroq, DefaultAsyncHttpxClient
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import json
import os
from db import get_game, update_game
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncClient
from prompts import char_createn

load_dotenv()
router = Router()


class MakingCharacter(StatesGroup):
    MakingCharacter = State()


@router.message(CommandStart(deep_link=True, magic=F.args.contains('char_')))
async def char_create( message: Message,command: CommandObject, session: AsyncSession,
                      state: FSMContext):
    game_id = int(command.args.split('_')[1])
    chat_id = int(command.args.split('_')[2])
    game_data = await get_game(game_id, session)
    game_data = game_data[0]
    real_game_data = json.loads(game_data.game_data)
    game_data = real_game_data
    dct = {"GAME_STATE": game_data}
    dct['characters_creation'] = "True"
    game_data = dct
    await state.set_state(MakingCharacter.MakingCharacter)
    await state.set_data({'game_data': game_data, 'game_id': game_id, 'chat_id': chat_id})
    menu_generate_purpose = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Давай начнём создавать персонажа!')]],
        resize_keyboard=True, one_time_keyboard=True)
    await message.answer('Начнём создавать персонажа!', keyboard=menu_generate_purpose)



@router.message(MakingCharacter.MakingCharacter)
async def still_char_create(message: Message, session: AsyncSession,
                            groq_client: (AsyncGroq if os.getenv('USE_OPENAI') == "False" else AsyncClient),
                            # groq_client: AsyncClient,
                            state: FSMContext):
    data = await state.get_data()
    game_id = data['game_id']
    chat_id = data['chat_id']
    data = data['game_data']
    chr_creation = data['characters_creation']
    if chr_creation != 'False':
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                char_createn(data, message.from_user.id),
                {
                    'role': 'user',
                    'content': message.text
                }
            ],
            model=os.getenv("MODEL"),
            response_format={'type': 'json_object'}
            # model='gpt-4o'
        )
        ans = chat_completion.choices[0].message.content
        print(ans)
        ans = json.loads(ans)
        try:
            await message.answer(ans['message'])
            await state.set_data({'game_data': ans, 'game_id': game_id, 'chat_id': chat_id})
            if ans['characters_creation'] == 'False' or ans['characters_creation'] == False:
                gd = await get_game(game_id, session)
                gd = gd[0]
                gd = gd.game_data
                gd = json.loads(gd)

                try:
                    chr_lst = gd['CHARACTERS']
                except:
                    chr_lst = []
                chr_lst.append(ans['game_data']['CHARACTER'][0])
                gd['CHARACTERS'] = chr_lst
                await update_game(game_id, {"game_data": json.dumps(gd)}, session)
                await message.answer("Готово! Персонаж создан и добавлен в игру!")
                await state.clear()
        except Exception as e:
            print("Ошибка!", type(e).__name__)
            await message.answer('Упс! Отправь, пожалуйста, сообщение ещё раз')

    else:
        await message.answer("Готово! Персонаж создан и добавлен в игру!")
        await state.clear()


@router.message(F.data == 'generate_game')
async def start_of_the_DND(message: Message, session: AsyncSession,
                           groq_client: AsyncGroq,
                           # groq_client: AsyncClient,
                           state: FSMContext):
    data = await state.get_data()
    data = data['game_data']

