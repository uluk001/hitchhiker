from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from datetime import time as dt_time
from threading import Lock
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    delete,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

FileID = str


@dataclass
class Trip:
    id: UUID
    driver_id: int
    from_city: str
    to_city: str
    departure_date: date
    time: Optional[dt_time]
    seats: int
    price: Optional[str]
    phone: str
    car: Optional[str]
    photos: List[FileID]
    comment: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class Storage:
    async def create_trip(self, trip: Trip) -> None:
        raise NotImplementedError

    async def search_trips(self, from_city: str, to_city: str, departure_date: date) -> List[Trip]:
        raise NotImplementedError

    async def get_trip(self, trip_id: UUID) -> Optional[Trip]:
        raise NotImplementedError

    async def delete_trip(self, trip_id: UUID) -> None:
        raise NotImplementedError

    async def update_trip(self, trip_id: UUID, data: dict) -> None:
        raise NotImplementedError

    async def list_driver_trips(self, driver_id: int) -> List[Trip]:
        raise NotImplementedError

    async def record_contact(self, trip_id: UUID, passenger_id: int) -> None:
        raise NotImplementedError

    async def set_language(self, user_id: int, language: str) -> None:
        raise NotImplementedError

    async def get_language(self, user_id: int, default: str = 'ru') -> str:
        raise NotImplementedError


class MemoryStorage(Storage):
    def __init__(self) -> None:
        self._trips: Dict[UUID, Trip] = {}
        self._contacts: Dict[UUID, List[int]] = {}
        self._languages: Dict[int, str] = {}
        self._lock = Lock()

    async def create_trip(self, trip: Trip) -> None:
        with self._lock:
            self._trips[trip.id] = trip

    async def search_trips(self, from_city: str, to_city: str, departure_date: date) -> List[Trip]:
        with self._lock:
            return [
                t for t in self._trips.values()
                if t.from_city == from_city and t.to_city == to_city and t.departure_date == departure_date
            ]

    async def get_trip(self, trip_id: UUID) -> Optional[Trip]:
        with self._lock:
            return self._trips.get(trip_id)

    async def delete_trip(self, trip_id: UUID) -> None:
        with self._lock:
            self._trips.pop(trip_id, None)
            self._contacts.pop(trip_id, None)

    async def update_trip(self, trip_id: UUID, data: dict) -> None:
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip:
                return
            for k, v in data.items():
                setattr(trip, k, v)

    async def list_driver_trips(self, driver_id: int) -> List[Trip]:
        with self._lock:
            return [t for t in self._trips.values() if t.driver_id == driver_id]

    async def record_contact(self, trip_id: UUID, passenger_id: int) -> None:
        with self._lock:
            self._contacts.setdefault(trip_id, []).append(passenger_id)

    async def set_language(self, user_id: int, language: str) -> None:
        with self._lock:
            self._languages[user_id] = language

    async def get_language(self, user_id: int, default: str = 'ru') -> str:
        with self._lock:
            return self._languages.get(user_id, default)


class Base(DeclarativeBase):
    pass


class TripModel(Base):
    __tablename__ = 'trips'

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_city: Mapped[str] = mapped_column(String, nullable=False)
    to_city: Mapped[str] = mapped_column(String, nullable=False)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[Optional[dt_time]] = mapped_column(Time)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Optional[str]] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    car: Mapped[Optional[str]] = mapped_column(String)
    photos: Mapped[List[FileID]] = mapped_column(JSON, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @classmethod
    def from_dataclass(cls, trip: Trip) -> 'TripModel':
        return cls(
            id=trip.id,
            driver_id=trip.driver_id,
            from_city=trip.from_city,
            to_city=trip.to_city,
            departure_date=trip.departure_date,
            time=trip.time,
            seats=trip.seats,
            price=trip.price,
            phone=trip.phone,
            car=trip.car,
            photos=trip.photos,
            comment=trip.comment,
            created_at=trip.created_at,
        )

    def to_dataclass(self) -> Trip:
        return Trip(
            id=self.id,
            driver_id=self.driver_id,
            from_city=self.from_city,
            to_city=self.to_city,
            departure_date=self.departure_date,
            time=self.time,
            seats=self.seats,
            price=self.price,
            phone=self.phone,
            car=self.car,
            photos=self.photos,
            comment=self.comment,
            created_at=self.created_at,
        )


class ContactModel(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('trips.id'))
    passenger_id: Mapped[int] = mapped_column(Integer, nullable=False)


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    language: Mapped[str] = mapped_column(String, nullable=False)


class SQLStorage(Storage):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self._session_maker = session_maker

    @classmethod
    async def create(cls, url: str) -> 'SQLStorage':
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        return cls(session_maker)

    async def create_trip(self, trip: Trip) -> None:
        async with self._session_maker() as session:
            session.add(TripModel.from_dataclass(trip))
            await session.commit()

    async def search_trips(self, from_city: str, to_city: str, departure_date: date) -> List[Trip]:
        async with self._session_maker() as session:
            result = await session.execute(
                select(TripModel).where(
                    TripModel.from_city == from_city,
                    TripModel.to_city == to_city,
                    TripModel.departure_date == departure_date,
                )
            )
            return [row[0].to_dataclass() for row in result.all()]

    async def get_trip(self, trip_id: UUID) -> Optional[Trip]:
        async with self._session_maker() as session:
            obj = await session.get(TripModel, trip_id)
            return obj.to_dataclass() if obj else None

    async def delete_trip(self, trip_id: UUID) -> None:
        async with self._session_maker() as session:
            await session.execute(delete(TripModel).where(TripModel.id == trip_id))
            await session.commit()

    async def update_trip(self, trip_id: UUID, data: dict) -> None:
        async with self._session_maker() as session:
            await session.execute(update(TripModel).where(TripModel.id == trip_id).values(**data))
            await session.commit()

    async def list_driver_trips(self, driver_id: int) -> List[Trip]:
        async with self._session_maker() as session:
            result = await session.execute(select(TripModel).where(TripModel.driver_id == driver_id))
            return [row[0].to_dataclass() for row in result.all()]

    async def record_contact(self, trip_id: UUID, passenger_id: int) -> None:
        async with self._session_maker() as session:
            session.add(ContactModel(trip_id=trip_id, passenger_id=passenger_id))
            await session.commit()

    async def set_language(self, user_id: int, language: str) -> None:
        async with self._session_maker() as session:
            obj = await session.get(UserModel, user_id)
            if obj:
                obj.language = language
            else:
                session.add(UserModel(id=user_id, language=language))
            await session.commit()

    async def get_language(self, user_id: int, default: str = 'ru') -> str:
        async with self._session_maker() as session:
            obj = await session.get(UserModel, user_id)
            return obj.language if obj else default
