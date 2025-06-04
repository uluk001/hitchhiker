from __future__ import annotations

import uuid
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from ..storage import Trip, MemoryStorage
from ..utils import validate_phone
from datetime import date

router = Router()


class CreateTrip(StatesGroup):
    from_city = State()
    to_city = State()
    date = State()
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
    await state.set_state(CreateTrip.date)
    await message.answer('Дата в формате YYYY-MM-DD')


@router.message(CreateTrip.date)
async def set_date(message: Message, state):
    await state.update_data(date=message.text)
    await state.set_state(CreateTrip.phone)
    await message.answer('Номер телефона')


@router.message(CreateTrip.phone)
async def set_phone(message: Message, state):
    if not validate_phone(message.text):
        await message.answer('Неверный формат телефона')
        return
    data = await state.update_data(phone=message.text)
    trip = Trip(
        id=uuid.uuid4(),
        driver_id=message.from_user.id,
        from_city=data['from_city'],
        to_city=data['to_city'],
        date=date.fromisoformat(data['date']),
        time=None,
        seats=1,
        price=None,
        phone=data['phone'],
        car=None,
        photos=[],
        comment=None,
    )
    storage: MemoryStorage = message.bot['storage']
    storage.create_trip(trip)
    await message.answer('Поездка создана')
    await state.clear()
