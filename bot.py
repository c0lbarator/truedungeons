from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, LinkPreviewOptions
from aiogram.client.default import DefaultBotProperties
import asyncio
import os
from dotenv import load_dotenv
import game
from aiogram.fsm.storage.redis import RedisStorage
from modified_redis import DefaultKeyBuilder
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient
from middlewares.db import DbSessionMiddleware
from groq import AsyncGroq, DefaultAsyncHttpxClient
import char_creation_new
import enroll
import dungeon_master
from openai import AsyncClient as Azaza
from openai import DefaultAsyncHttpxClient as DAHC
from requests_html import AsyncHTMLSession
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
redis_url = os.getenv("REDIS_URL")
bot = Bot(token=bot_token,
          default=DefaultBotProperties(link_preview=LinkPreviewOptions(is_disabled=True)))
async def main():
    storage = RedisStorage.from_url(redis_url, key_builder=DefaultKeyBuilder())
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    asyncclient = AsyncClient()
    groqclient = AsyncGroq(
        api_key=os.getenv('GROQ_KEY'),
        http_client=DefaultAsyncHttpxClient(
            proxies=os.getenv('PROXY')
        )
    ) if os.getenv("USE_OPENAI") == "False" else Azaza(
        #base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('OPENAI_KEY'),
        #api_key=os.getenv("OPENROUTER_KEY"),
        http_client=DAHC(
            proxies=os.getenv('PROXY')
        )
    )
    asession = AsyncHTMLSession()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker, groqclient=groqclient, asession=asession))
    dp.include_routers(char_creation_new.router, enroll.router, dungeon_master.router, game.router)
    await dp.start_polling(bot)
if __name__ == '__main__':
    asyncio.run(main())