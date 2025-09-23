from sqlalchemy import select

from db.models import TagModel
from db.repository.base import BaseSqlAlchemyRepo


class TagRepo(BaseSqlAlchemyRepo):
    async def get_by_name(self, name: str) -> TagModel | None:
        stmt = select(TagModel).where(TagModel.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, name: str) -> TagModel:
        tag = TagModel(name=name)
        self.session.add(tag)
        return tag

    async def get_or_create(self, name: str) -> TagModel:
        tag = await self.get_by_name(name)
        if tag:
            return tag
        return await self.create(name)
