from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert

from db.models import UserModel
from db.repository.base import BaseSqlAlchemyRepo


class UserModelRepo(BaseSqlAlchemyRepo):
    async def get_by_tg_id(self, tg_id: int) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.tg_id == tg_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(
        self,
        tg_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        stmt = (
            insert(UserModel)
            .values(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            .on_conflict_do_nothing()
        )
        await self.session.execute(stmt)
