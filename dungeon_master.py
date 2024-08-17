from aiogram import Router, F, html, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, BufferedInputFile, URLInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from groq import AsyncGroq, DefaultAsyncHttpxClient
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import json
import os
from db import get_game, create_game
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncClient
from requests_html import AsyncHTMLSession
from bot import bot
import asyncio
from prompts import dm, creative, analytics
import random
load_dotenv()
router = Router()


class PlayingGame(StatesGroup):
    PlayingGame = State()



@router.callback_query(F.data.contains("launch_"))
async def char_create(callback: CallbackQuery, session: AsyncSession,
                      state: FSMContext):
    game_id = int(callback.data.split('_')[1])
    game_data = await get_game(game_id, session)
    game_data = game_data[0]
    real_game_data = json.loads(game_data.game_data)
    game_data = real_game_data
    await state.set_state(PlayingGame.PlayingGame)
    await state.set_data({'game_data': game_data})
    await callback.message.answer('Игра началась!\n'
                                  'Чтобы ответить Мастеру, ответь на его сообщение')



@router.message(Command('save'),
                PlayingGame.PlayingGame)
async def saving_game(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    data = json.dumps(data)
    game = await create_game({"game_data": data}, session)
    game_resume = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Присоединиться!', callback_data=f'launch_{game}')]
        ]
    )
    await message.answer(
        "Игра сохранена! Для возобновления игры с текущего сохранения нажми кнопку ниже\n"
        "P.S. Хочешь запустить игру сам? Переходи в @trueDnDbot и следуй инструкциям мастера!",
        reply_markup=game_resume
    )
@router.message(Command('stop'),PlayingGame.PlayingGame)
async def stop_game(message: Message, groq_client:(AsyncGroq if os.getenv('USE_OPENAI') == "False" else AsyncClient), state: FSMContext):
    data = await state.get_data()
    print(data)
    chat_completion = await groq_client.with_options(max_retries=3).chat.completions.create(
        messages=[
            analytics,
            {
                'role': 'user',
                'content': f'Данные об игре:{data}'
            }
        ],
        model=os.getenv("MODEL")
    )
    print(chat_completion)
    ans = chat_completion.choices[0].message.content
    await message.answer(ans)
    await message.answer("Игра завершена, спасибо за сессию!\n"
                         "P.S. Хочешь запустить игру сам? Переходи в @trueDnDbot и следуй инструкциям мастера!")
    await state.clear()
@router.message(PlayingGame.PlayingGame, F.reply_to_message.from_user.id == 7271196938)
@router.message(PlayingGame.PlayingGame, F.content.type == 'voice', F.reply_to_message.from_user.id == 7271196938)
async def start_of_the_DND(message: Message, session: AsyncSession,
                            groq_client: (AsyncGroq if os.getenv('USE_OPENAI') == "False" else AsyncClient),
                            state: FSMContext, asession: AsyncHTMLSession):
    data = await state.get_data()
    data = data['game_data']
    #all_users = data["CHARACTERS"]  # --> list
    #game_state = data["GAME_STATE"]  # --> dict
    #recent_action = data["RECENT_ACTIONS"]  # --> list
    #conflict_state = data["CONFLICT_STATE"]  # --> dict
    #rules = data["RULES"]  # --> str
    try:
        dmq = data['META']['quest']
    except:
        data['META'] = {}
        data['META']['quest'] = 5
    mt = message.text
    if data['META']['quest'] != 0:
        if message.voice:
            await bot.download(
                message.voice,
                destination=f'/tmp/{message.voice.file_id}.ogg'
            )
            mt = await groq_client.audio.transcriptions.create(
                model="whisper-1" if os.getenv("USE_OPENAI") == 'True' else "whisper-large-v3",
                file=open(f"/tmp/{message.voice.file_id}.ogg", "rb")
            )
            mt = mt.text
        chat_completion = await groq_client.with_options(max_retries=3).chat.completions.create(
            messages=[
                dm(data),
                {
                    'role': 'user',
                    'content': f"ID игрока: {message.from_user.id}\n {mt}"
                }
            ],
            response_format={'type': 'json_object'},
            # model='llama-3.1-70b-versatile'
            model=os.getenv("MODEL")
            #model="microsoft/wizardlm-2-8x22b"
        )
        ans = chat_completion.choices[0].message.content
        print(ans)
        try:
            ans = json.loads(ans)
            if ans['need_rescue_throw'] == "True" or ans['need_rescue_throw'] == True:
                await message.answer(ans['message'])
                await message.answer('Бросаю d20...')
                await asyncio.sleep(3)
                rescue_throw_result = random.randint(1, 20)
                await message.answer(f"Выпала {rescue_throw_result}")
                chat_completion = await groq_client.with_options(max_retries=3).chat.completions.create(
                    messages=[
                        dm(data),
                        {
                            'role': 'user',
                            'content': f"ID игрока: {message.from_user.id}\n {mt}"
                        },
                        {
                            'role':'assistant',
                            'content': ans['message']
                        },
                        {
                            'role': 'user',
                            'content': f"Результат спасброска: {rescue_throw_result}"
                        }
                    ],
                    response_format={'type': 'json_object'},
                    # model='llama-3.1-70b-versatile'
                    model=os.getenv("MODEL")
                    #model="microsoft/wizardlm-2-8x22b"
                )
                ans = chat_completion.choices[0].message.content
                print(ans)
                ans = json.loads(ans)
            await state.set_data({'game_data': ans})
            if ans.get('message', '0') == '0' or (ans['game_ended'] == 'True' or ans['game_ended'] == True):
                chat_completion = await groq_client.with_option(max_retries=3).chat.completions.create(
                    messages=[
                        analytics,
                        data
                    ]
                )
                ans = chat_completion.choices[0].message.content
                await message.answer(ans)
                await message.answer(
                    "Игра завершена, всем спасибо за сессию!\n"
                    f"Чтобы узнать сводку о себе, посмотри свой ID в сообщении о записи на игру или в профиле в {html.link("боте", "https://t.me/truedndbot")}\n"
                    "P.S. Хочешь запустить игру сам? Переходи в @trueDnDbot и следуй инструкциям мастера!"
                )
                await state.clear()
            else:
                chat_completion = await groq_client.with_options(max_retries=3).chat.completions.create(
                    messages=[
                        creative,
                        {
                            'role': 'user',
                            'content': f"{ans}"
                        }
                    ],
                    response_format={'type': 'json_object'},
                    # model='llama-3.1-70b-versatile'
                    model=os.getenv("MODEL")
                )
                img = chat_completion.choices[0].message.content
                img = json.loads(img)
                if img['need_image'] == 'True' or img['need_image'] == True:
                    try:
                        msg_id = await message.answer_photo('AgACAgIAAyEGAASC0XT5AAICq2a_CdCVTGWWb6zMfkT2WtcpxsVlAAIo3DEbT_f4SYFIO_G0Xd0BAQADAgADeQADNQQ',ans['message'])
                    except:
                        msg_id = await message.answer_photo(URLInputFile("https://gist.github.com/assets/77036902/1dff3450-d03e-4c69-b5e0-1a75dec57c23"), ans['message'])
                        print("Seems like you changed the bot. Please, replace photo id on line 188 with this:", msg_id.photo[-1].file_id)
                    chat_id = msg_id.chat.id
                    msg_id = msg_id.message_id
                    if img['need_sound'] == 'True' or img['need_sound'] == True:
                        res = await asession.get("https://freesound.org/apiv2/search/text/?query="+img['query']+"&token="+os.getenv("FS_KEY"))
                        print(img['query'])
                        sound_id = res.json()
                        print(sound_id)
                        if sound_id['count'] != 0:
                            sound_id = sound_id['results'][0]['id']
                            sound = await asession.get("https://freesound.org/apiv2/sounds/"+str(sound_id), headers={"Authorization":f"Token {os.getenv("FS_KEY")}"})
                            sound = sound.json()
                            print(sound)
                            sound_url = sound['previews']['preview-hq-mp3']
                            sound = URLInputFile(sound_url, filename=f"{img['query']}.mp3")
                            await message.answer_audio(sound)
                    '''response = await groq_client.images.generate(
                        model="dall-e-3",
                        prompt=img['prompt'],
                        size="1024x1024",
                        quality="standard",
                        n=1,
                    )'''
                    headers = {'x-api-key': os.getenv('SEGMIND_KEY')}
                    attempts = 10
                    URL = "https://api.segmind.com/v1/flux-schnell";
                    data = {
                        "prompt": img['prompt'],
                        "steps": 4,
                        "seed": 123456789,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "samples": 1,
                        "width": 1024,
                        "height": 1024,
                        "denoise": 1
                    }
                    while attempts > 0:
                       res = await asession.post(URL, headers=headers, json=data)
                       if res.status_code == 200:
                           pic = BufferedInputFile(res.content, filename="idk.jpeg")
                           await bot.edit_message_media(
                               media=InputMediaPhoto(media=pic, caption=ans['message']),
                               chat_id=chat_id, message_id=msg_id)
                           break
                       attempts-=1
                       await asyncio.sleep(10)

                else:
                    await message.answer(ans['message']+'.')
        except Exception as e:
            print("Ошибка!", type(e).__name__)
            await message.answer("Упс! Можешь, пожалуйста, повторить ещё раз?")
    else:
        await message.answer(
            "Игра завершена, всем спасибо за сессию!\n"
            f"Чтобы узнать сводку о себе, посмотри свой ID в сообщении о записи на игру или в профиле в {html.link("боте", "https://t.me/truedndbot")}\n"
            "P.S. Хочешь запустить игру сам? Переходи в @trueDnDbot и следуй инструкциям мастера!"
        )
        await message.answer(str(data))
        await state.clear()