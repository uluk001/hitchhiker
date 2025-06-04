from __future__ import annotations

import uuid
from datetime import date

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..storage import Storage, Trip
from ..utils import validate_phone

router = Router()


class CreateTrip(StatesGroup):
    from_city = State()
    to_city = State()
    departure_date = State()
    phone = State()
    confirm = State()


@router.message(F.text == 'create')
async def cmd_create(message: Message, state):
    await state.set_state(CreateTrip.from_city)
    await message.answer('Откуда?')


@router.message(CreateTrip.from_city)
async def set_from_city(message: Message, state):
    await state.update_data(from_city=message.text)
    await state.set_state(CreateTrip.to_city)
    await message.answer('Куда?')


@router.message(CreateTrip.to_city)
async def set_to_city(message: Message, state):
    await state.update_data(to_city=message.text)
    await state.set_state(CreateTrip.departure_date)
    await message.answer('Дата в формате YYYY-MM-DD')


@router.message(CreateTrip.departure_date)
async def set_departure_date(message: Message, state):
    await state.update_data(departure_date=message.text)
    await state.set_state(CreateTrip.phone)
    await message.answer('Номер телефона')


@router.message(CreateTrip.phone)
async def set_phone(message: Message, state, storage: Storage):
    if not validate_phone(message.text):
        await message.answer('Неверный формат телефона')
        return
    data = await state.update_data(phone=message.text)
    trip = Trip(
        id=uuid.uuid4(),
        driver_id=message.from_user.id,
        from_city=data['from_city'],
        to_city=data['to_city'],
        departure_date=date.fromisoformat(data['departure_date']),
        time=None,
        seats=1,
        price=None,
        phone=data['phone'],
        car=None,
        photos=[],
        comment=None,
    )
    await storage.create_trip(trip)
    await message.answer('Поездка создана')
    await state.clear()
