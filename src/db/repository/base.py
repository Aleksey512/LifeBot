from sqlalchemy.ext.asyncio import AsyncSession


class BaseSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
