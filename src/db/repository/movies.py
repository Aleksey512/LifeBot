from typing import Any, Optional, Sequence, overload

from sqlalchemy import delete, desc, select

from db.models import MovieModel
from db.repository.base import BaseSqlAlchemyRepo

HasNext = bool


class MoviesRepository(BaseSqlAlchemyRepo):
    @overload
    async def get(self) -> Sequence[MovieModel]: ...
    @overload
    async def get(self, *, mid: int) -> MovieModel | None: ...

    async def get(self, mid: Optional[int] = None) -> Any:
        if mid is None:
            result = await self.session.execute(select(MovieModel))
            return result.scalars().all()

        result = await self.session.execute(
            select(MovieModel).where(MovieModel.id == mid)
        )
        return result.scalar_one_or_none()

    async def get_by_is_watched(
        self, is_watched: bool, skip: int = 0, page_limit: int = 1
    ) -> tuple[Sequence[MovieModel], HasNext]:
        stmt = (
            select(MovieModel)
            .where(MovieModel.watched == is_watched)
            .order_by(desc(MovieModel.created_at))
            .limit(page_limit + 1)
            .offset(skip)
        )

        res = await self.session.execute(stmt)
        balances = res.scalars().all()

        has_next = len(balances) > page_limit
        if has_next:
            balances = balances[:page_limit]

        return balances, has_next

    async def create(
        self, title: str, year: int, description: Optional[str], poster: Optional[str]
    ) -> MovieModel:
        entity = MovieModel(
            title=title,
            year=year,
            description=description,
            poster=poster,
            watched=False,
        )
        self.session.add(entity)
        return entity

    async def delete(self, mid: int) -> None:
        stmt = delete(MovieModel).where(MovieModel.id == mid)
        await self.session.execute(stmt)
