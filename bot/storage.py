from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from threading import Lock


FileID = str


@dataclass
class Trip:
    id: UUID
    driver_id: int
    from_city: str
    to_city: str
    date: date
    time: Optional[time]
    seats: int
    price: Optional[str]
    phone: str
    car: Optional[str]
    photos: List[FileID]
    comment: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class Storage:
    def create_trip(self, trip: Trip) -> None:
        raise NotImplementedError

    def search_trips(self, from_city: str, to_city: str, date: date) -> List[Trip]:
        raise NotImplementedError

    def get_trip(self, trip_id: UUID) -> Optional[Trip]:
        raise NotImplementedError

    def delete_trip(self, trip_id: UUID) -> None:
        raise NotImplementedError

    def update_trip(self, trip_id: UUID, data: dict) -> None:
        raise NotImplementedError

    def list_driver_trips(self, driver_id: int) -> List[Trip]:
        raise NotImplementedError

    def record_contact(self, trip_id: UUID, passenger_id: int) -> None:
        raise NotImplementedError


class MemoryStorage(Storage):
    def __init__(self) -> None:
        self._trips: Dict[UUID, Trip] = {}
        self._contacts: Dict[UUID, List[int]] = {}
        self._lock = Lock()

    def create_trip(self, trip: Trip) -> None:
        with self._lock:
            self._trips[trip.id] = trip

    def search_trips(self, from_city: str, to_city: str, date: date) -> List[Trip]:
        with self._lock:
            return [
                t for t in self._trips.values()
                if t.from_city == from_city and t.to_city == to_city and t.date == date
            ]

    def get_trip(self, trip_id: UUID) -> Optional[Trip]:
        with self._lock:
            return self._trips.get(trip_id)

    def delete_trip(self, trip_id: UUID) -> None:
        with self._lock:
            self._trips.pop(trip_id, None)
            self._contacts.pop(trip_id, None)

    def update_trip(self, trip_id: UUID, data: dict) -> None:
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip:
                return
            for k, v in data.items():
                setattr(trip, k, v)

    def list_driver_trips(self, driver_id: int) -> List[Trip]:
        with self._lock:
            return [t for t in self._trips.values() if t.driver_id == driver_id]

    def record_contact(self, trip_id: UUID, passenger_id: int) -> None:
        with self._lock:
            self._contacts.setdefault(trip_id, []).append(passenger_id)
