import logging
import time
from typing import Any, NamedTuple, Optional, Sequence, TypeVarTuple, Unpack, overload

from sqlalchemy import case, delete, func, literal, select, update

from db.models import BalanceCategoryModel, BalanceModel
from db.repository.base import BaseSqlAlchemyRepo

logger = logging.getLogger(__name__)


class CategoryWithLimit(NamedTuple):
    category: BalanceCategoryModel
    limit: float


_Ts = TypeVarTuple("_Ts")  # для нескольких полей


class CategoryRepo(BaseSqlAlchemyRepo):
    # 1. Без аргументов → список моделей
    @overload
    async def get(self) -> Sequence[BalanceCategoryModel]: ...

    # 2. По id → модель или None
    @overload
    async def get(self, *, id: int) -> BalanceCategoryModel | None: ...

    # 3. Только поля → список кортежей
    @overload
    async def get(self, *fields: Unpack[_Ts]) -> list[tuple[Unpack[_Ts]]]: ...

    # 4. id + поля → один кортеж или None
    @overload
    async def get(self, *fields: Unpack[_Ts], id: int) -> tuple[Unpack[_Ts]] | None: ...

    async def get(self, *fields: Any, id: int | None = None) -> Any:  # type: ignore
        stmt = select(*fields) if fields else select(BalanceCategoryModel)

        if id is not None:
            stmt = stmt.where(BalanceCategoryModel.id == id)

        result = await self.session.execute(stmt)

        if id is not None:
            if fields:
                return result.first()
            return result.scalar_one_or_none()

        if fields:
            return result.all()
        return result.scalars().all()

    async def get_with_cur_limit(self) -> list[CategoryWithLimit]:
        stmt = (
            select(
                BalanceCategoryModel,
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (BalanceModel.type == "expense")
                                & (
                                    BalanceModel.created_at
                                    >= BalanceCategoryModel.last_reset
                                ),
                                BalanceModel.amount,
                            ),
                            else_=literal(0),
                        )
                    ),
                    0,
                ).label("current_expense"),
            )
            .outerjoin(
                BalanceModel, BalanceModel.category_id == BalanceCategoryModel.id
            )
            .group_by(BalanceCategoryModel.id)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        return [CategoryWithLimit(category=row[0], limit=row[1]) for row in rows]

    async def create(
        self, name: str, max_limit: Optional[float], last_reset: int
    ) -> BalanceCategoryModel:
        entity = BalanceCategoryModel(
            name=name, max_limit=max_limit, last_reset=last_reset
        )
        self.session.add(entity)
        return entity

    async def update(self, cid: int, **updates: Any) -> None:
        stmt = (
            update(BalanceCategoryModel)
            .where(BalanceCategoryModel.id == cid)
            .values(**updates)
        )
        await self.session.execute(stmt)

    async def reset_all_limits(self) -> None:
        current_ts = int(time.time())
        stmt = update(BalanceCategoryModel).values(last_reset=current_ts)
        await self.session.execute(stmt)

    async def delete(self, cid: int) -> None:
        stmt = delete(BalanceCategoryModel).where(BalanceCategoryModel.id == cid)
        await self.session.execute(stmt)
