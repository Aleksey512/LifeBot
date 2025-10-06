import datetime
import time
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BaseWithID(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True
    )


class BaseWithDate(Base):
    __abstract__ = True
    created_at: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        default=lambda: int(time.time()),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        default=lambda: int(time.time()),
        onupdate=lambda: int(time.time()),
        nullable=False,
        index=True,
    )

    @property
    def created_at_readable(self) -> str:
        return datetime.datetime.fromtimestamp(self.created_at).strftime(
            "%d.%m.%Y %H:%M"
        )

    @property
    def updated_at_readable(self) -> str:
        return datetime.datetime.fromtimestamp(self.updated_at).strftime(
            "%d.%m.%Y %H:%M"
        )


# ------------------- Таблицы -------------------


class UserModel(BaseWithDate):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        unique=True,
        nullable=False,
        primary_key=True,
    )
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class BalanceCategoryModel(BaseWithID, BaseWithDate):
    __tablename__ = "balance_category"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    max_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_reset: Mapped[int] = mapped_column(
        BigInteger(), default=lambda: int(time.time())
    )

    balances: Mapped[List["BalanceModel"]] = relationship(
        "BalanceModel", back_populates="category"
    )

    @property
    def last_reset_readable(self) -> str:
        return datetime.datetime.fromtimestamp(self.last_reset).strftime(
            "%d.%m.%Y %H:%M"
        )


class TagModel(BaseWithID, BaseWithDate):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    balances: Mapped[List["BalanceModel"]] = relationship(
        "BalanceModel", secondary="balance_tags", back_populates="tags"
    )


# Промежуточная таблица many-to-many для тегов
balance_tags = Table(
    "balance_tags",
    Base.metadata,
    Column("balance_id", ForeignKey("balance.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class BalanceModel(BaseWithID, BaseWithDate):
    __tablename__ = "balance"

    type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # 'income' или 'expense'
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("balance_category.id", ondelete="CASCADE"), nullable=True
    )

    category: Mapped[Optional["BalanceCategoryModel"]] = relationship(
        "BalanceCategoryModel", back_populates="balances"
    )
    tags: Mapped[List["TagModel"]] = relationship(
        "TagModel", secondary=balance_tags, back_populates="balances"
    )

    @property
    def type_readable(self) -> str:
        return {"income": "Доход", "expense": "Расход"}.get(self.type, self.type)


class MovieModel(BaseWithID, BaseWithDate):
    __tablename__ = "movies"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    poster: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # tmdb / kinopoisk
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    watched: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    @property
    def status(self) -> str:
        return "Просмотренно" if self.watched else "Хочу посмотреть"


class SeriesModel(BaseWithID, BaseWithDate):
    __tablename__ = "series"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    poster: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # tmdb / kinopoisk
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    watched: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    watch_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'watching', 'completed', 'planned'
    season_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    episodes_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    episode_current: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season_current: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    @property
    def status(self) -> str:
        if self.watch_status == "completed":
            return "Просмотрено"
        if self.watch_status == "watching":
            return "Смотрю"
        if self.watch_status == "planned":
            return "Запланировано"
        return "Просмотренно" if self.watched else "Хочу посмотреть"
