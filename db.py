from sqlalchemy import Table, Column, String, Integer, MetaData, select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
meta = MetaData()
dnd_games_table = Table(
    'dnd_games',
    meta,
    Column('id', Integer, primary_key=True),
    Column('game_data', String),
)
engine = create_async_engine(os.getenv('DATABASE_URL'))
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)
    await engine.dispose()
async def create_game(game_info: dict, session: AsyncSession):
    id = await session.execute(
        dnd_games_table.insert().returning(dnd_games_table.c.id),
        [
            game_info
        ],

    )
    await session.commit()
    rt = id.scalar()
    return rt
async def get_game(game_id: int, session: AsyncSession):
    stmt = select(dnd_games_table).where(dnd_games_table.c.id == game_id)
    result = await session.execute(stmt)
    game = result.all()
    return game
async def update_game(game_id: int,game_info: dict, session: AsyncSession):
    stmt = update(dnd_games_table).where(dnd_games_table.c.id == game_id).values(**game_info)
    await session.execute(stmt)
    await session.commit()


if __name__ == '__main__':
    asyncio.run(create_db())