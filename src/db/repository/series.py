from typing import Any, Optional, Sequence, overload

from sqlalchemy import delete, desc, select

from db.models import SeriesModel
from db.repository.base import BaseSqlAlchemyRepo

HasNext = bool


class SeriesRepository(BaseSqlAlchemyRepo):
    @overload
    async def get(self) -> Sequence[SeriesModel]: ...
    @overload
    async def get(self, *, sid: int) -> SeriesModel | None: ...

    async def get(self, sid: Optional[int] = None) -> Any:
        if sid is None:
            result = await self.session.execute(select(SeriesModel))
            return result.scalars().all()

        result = await self.session.execute(
            select(SeriesModel).where(SeriesModel.id == sid)
        )
        return result.scalar_one_or_none()

    async def get_by_is_watched(
        self, is_watched: bool, skip: int = 0, page_limit: int = 1
    ) -> tuple[Sequence[SeriesModel], HasNext]:
        stmt = (
            select(SeriesModel)
            .where(SeriesModel.watched == is_watched)
            .order_by(desc(SeriesModel.created_at))
            .limit(page_limit + 1)
            .offset(skip)
        )

        res = await self.session.execute(stmt)
        series_list = res.scalars().all()

        has_next = len(series_list) > page_limit
        if has_next:
            series_list = series_list[:page_limit]

        return series_list, has_next

    async def get_by_watch_status(
        self, watch_status: str, skip: int = 0, page_limit: int = 1
    ) -> tuple[Sequence[SeriesModel], HasNext]:
        stmt = (
            select(SeriesModel)
            .where(SeriesModel.watch_status == watch_status)
            .order_by(desc(SeriesModel.created_at))
            .limit(page_limit + 1)
            .offset(skip)
        )

        res = await self.session.execute(stmt)
        series_list = res.scalars().all()

        has_next = len(series_list) > page_limit
        if has_next:
            series_list = series_list[:page_limit]

        return series_list, has_next

    async def create(
        self,
        title: str,
        year: int,
        description: Optional[str],
        poster: Optional[str],
        episode_current: Optional[int] = 1,
        season_current: Optional[int] = 1,
        season_number: Optional[int] = None,
        episodes_count: Optional[int] = None,
        watch_status: Optional[str] = "planned",
    ) -> SeriesModel:
        entity = SeriesModel(
            title=title,
            year=year,
            description=description,
            poster=poster,
            season_number=season_number,
            episodes_count=episodes_count,
            episode_current=episode_current,
            season_current=season_current,
            watched=False,
            watch_status=watch_status,
        )
        self.session.add(entity)
        return entity

    async def delete(self, sid: int) -> None:
        stmt = delete(SeriesModel).where(SeriesModel.id == sid)
        await self.session.execute(stmt)
