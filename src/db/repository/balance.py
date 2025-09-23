from typing import Sequence

from sqlalchemy import desc, select

from config.consts import DEFAULT_PAGE_LIMIT
from db.models import BalanceCategoryModel, BalanceModel, TagModel
from db.repository.base import BaseSqlAlchemyRepo

Count = int
HasNext = bool


class BalanceRepo(BaseSqlAlchemyRepo):
    async def get_by_category_and_last_reset(
        self, category_id: int, skip: int = 0
    ) -> tuple[Sequence[BalanceModel], HasNext]:
        stmt = (
            select(BalanceModel)
            .join(
                BalanceCategoryModel,
                BalanceModel.category_id == BalanceCategoryModel.id,
            )
            .where(
                BalanceCategoryModel.id == category_id,
                BalanceModel.created_at > BalanceCategoryModel.last_reset,
            )
            .order_by(desc(BalanceModel.created_at))
            .limit(DEFAULT_PAGE_LIMIT + 1)
            .offset(skip)
        )

        res = await self.session.execute(stmt)
        balances = res.scalars().all()

        has_next = len(balances) > DEFAULT_PAGE_LIMIT
        if has_next:
            balances = balances[:DEFAULT_PAGE_LIMIT]

        return balances, has_next

    async def create(
        self,
        name: str,
        amount: float,
        balance_type: str,
        category_id: int | None = None,
        tags: list[TagModel] | None = None,
    ) -> BalanceModel:
        balance = BalanceModel(
            name=name,
            amount=amount,
            type=balance_type,
            category_id=category_id,
            tags=tags or [],
        )
        self.session.add(balance)
        return balance
