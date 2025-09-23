from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import settings

Engine = create_async_engine(settings.DB_URL)
Session = async_sessionmaker(Engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Базовый контекстный менеджер для сессии"""
    async with Session() as session:
        yield session


@asynccontextmanager
async def transaction() -> AsyncIterator[AsyncSession]:
    """Отдельный контекстный менеджер для транзакции"""
    async with Session.begin() as session:
        yield session
