from typing import Callable, Awaitable, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from groq import AsyncGroq
from openai import AsyncClient
from dotenv import load_dotenv
from requests_html import AsyncHTMLSession
load_dotenv()
import os
class DbSessionMiddleware(BaseMiddleware):
    if os.getenv("USE_OPENAI") == "True":
        def __init__(self, session_pool: async_sessionmaker, groqclient: AsyncClient, asession: AsyncHTMLSession):
            super().__init__()
            self.session_pool = session_pool
            self.groq_client = groqclient
            self.asession = asession
        async def __call__(
                self,
                handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                event: TelegramObject,
                data: Dict[str, Any],
        ) -> Any:
            data['groq_client'] = self.groq_client
            data['asession'] = self.asession
            async with self.session_pool() as session:
                data["session"] = session
                return await handler(event, data)
    else:
        def __init__(self, session_pool: async_sessionmaker, groqclient: AsyncClient, asession: AsyncHTMLSession):
            super().__init__()
            self.session_pool = session_pool
            self.groq_client = groqclient
            self.asession = asession
        async def __call__(
                self,
                handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                event: TelegramObject,
                data: Dict[str, Any],
        ) -> Any:
            data['groq_client'] = self.groq_client
            data['asession'] = self.asession
            async with self.session_pool() as session:
                data["session"] = session
                return await handler(event, data)

