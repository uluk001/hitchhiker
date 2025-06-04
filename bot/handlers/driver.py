from __future__ import annotations

import uuid
from datetime import date, timedelta, time as dt_time

from aiogram import F, Router
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..config import Config
from ..i18n import t
from ..storage import Storage, Trip
from ..utils import build_keyboard, validate_phone, validate_time

router = Router()

SKIP = {"ru": "Пропустить", "kg": "Өткөрүү"}
AGREE = {"ru": "💬 Договорная", "kg": "💬 Келишимдүү"}


class CreateTrip(StatesGroup):
    from_city = State()
    to_city = State()
    date = State()
    time = State()
    seats = State()
    price = State()
    car = State()
    photos = State()
    phone = State()
    comment = State()
    confirm = State()


def city_kb(cfg: Config) -> list[tuple[str, str]]:
    return [(c, f"city:{c}") for c in cfg.cities]


def seats_kb() -> list[tuple[str, str]]:
    return [(str(i), f"seats:{i}") for i in range(1, 6)] + [("5+", "seats:5")]  # 5 means 5 or more


@router.message(F.text.startswith("🚗"))
async def start_create(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    await state.set_state(CreateTrip.from_city)
    kb = build_keyboard(city_kb(config))
    await message.answer(t(lang, "driver.from_city"), reply_markup=kb)


@router.callback_query(CreateTrip.from_city, F.data.startswith("city:"))
async def set_from(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await state.update_data(from_city=callback.data.split(":", 1)[1])
    await state.set_state(CreateTrip.to_city)
    await callback.message.edit_text(t(lang, "driver.to_city"), reply_markup=build_keyboard(city_kb(config)))
    await callback.answer()


@router.callback_query(CreateTrip.to_city, F.data.startswith("city:"))
async def set_to(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await state.update_data(to_city=callback.data.split(":", 1)[1])
    await state.set_state(CreateTrip.date)
    buttons = [
        ("Сегодня", "date:0"),
        ("Завтра", "date:1"),
        ("Введите дату", "date:manual"),
    ]
    await callback.message.edit_text(t(lang, "driver.date"), reply_markup=build_keyboard(buttons))
    await callback.answer()


@router.callback_query(CreateTrip.date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    data = callback.data.split(":", 1)[1]
    if data == "manual":
        await callback.message.edit_text(t(lang, "driver.date") + " YYYY-MM-DD")
        await state.set_state(CreateTrip.date)
        await state.update_data(manual_date=True)
    else:
        days = int(data)
        await state.update_data(date=date.today() + timedelta(days=days), manual_date=False)
        await state.set_state(CreateTrip.time)
        await callback.message.edit_text(t(lang, "driver.time"))
    await callback.answer()


@router.message(CreateTrip.date)
async def manual_date(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    try:
        chosen = date.fromisoformat(message.text)
    except ValueError:
        await message.answer(t(lang, "driver.date") + " YYYY-MM-DD")
        return
    await state.update_data(date=chosen)
    await state.set_state(CreateTrip.time)
    await message.answer(t(lang, "driver.time"))


@router.message(CreateTrip.time)
async def set_time(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    if message.text == SKIP[lang]:
        await state.update_data(time=None)
    elif validate_time(message.text):
        await state.update_data(time=dt_time.fromisoformat(message.text))
    else:
        await message.answer(t(lang, "driver.time"))
        return
    await state.set_state(CreateTrip.seats)
    await message.answer(t(lang, "driver.seats"), reply_markup=build_keyboard(seats_kb()))


@router.callback_query(CreateTrip.seats, F.data.startswith("seats:"))
async def set_seats(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    seats = int(callback.data.split(":", 1)[1])
    await state.update_data(seats=seats)
    await state.set_state(CreateTrip.price)
    kb = build_keyboard([(AGREE[lang], "price:none")])
    await callback.message.edit_text(t(lang, "driver.price"), reply_markup=kb)
    await callback.answer()


@router.callback_query(CreateTrip.price, F.data.startswith("price:none"))
async def price_agree(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await state.update_data(price=None)
    await state.set_state(CreateTrip.car)
    await callback.message.edit_text(t(lang, "driver.car"))
    await callback.answer()


@router.message(CreateTrip.price)
async def set_price(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    await state.update_data(price=message.text)
    await state.set_state(CreateTrip.car)
    await message.answer(t(lang, "driver.car"))


@router.message(CreateTrip.car)
async def set_car(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    if message.text == SKIP[lang]:
        await state.update_data(car=None)
    else:
        await state.update_data(car=message.text)
    await state.set_state(CreateTrip.photos)
    await message.answer(t(lang, "driver.photos"))


@router.message(CreateTrip.photos, F.photo)
async def collect_photo(message: Message, state: FSMContext, storage: Storage, config: Config) -> None:
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    if len(photos) >= 3:
        await state.update_data(photos=photos)
        await state.set_state(CreateTrip.phone)
        lang = await storage.get_language(message.from_user.id, config.default_language)
        await message.answer(t(lang, "driver.phone"))
    else:
        await state.update_data(photos=photos)


@router.message(CreateTrip.photos)
async def skip_photos(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    if message.text == SKIP[lang]:
        await state.update_data(photos=[])
        await state.set_state(CreateTrip.phone)
        await message.answer(t(lang, "driver.phone"))
    else:
        await message.answer(t(lang, "driver.photos"))


@router.message(CreateTrip.phone, F.contact)
async def phone_contact(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(CreateTrip.comment)
    lang = await storage.get_language(message.from_user.id, config.default_language)
    await message.answer(t(lang, "driver.comment"))


@router.message(CreateTrip.phone)
async def phone_text(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    if not validate_phone(message.text):
        await message.answer(t(lang, "driver.phone"))
        return
    await state.update_data(phone=message.text)
    await state.set_state(CreateTrip.comment)
    await message.answer(t(lang, "driver.comment"))


@router.message(CreateTrip.comment)
async def set_comment(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    if message.text == SKIP[lang]:
        await state.update_data(comment=None)
    else:
        await state.update_data(comment=message.text)
    await state.set_state(CreateTrip.confirm)
    data = await state.get_data()
    preview = f"{data['from_city']} ➡️ {data['to_city']}\n{data['date']}"
    if data.get('time'):
        preview += f" {data['time'].strftime('%H:%M')}"
    preview += f"\n{data['seats']} seats"
    if data.get('price'):
        preview += f" — {data['price']}"
    else:
        preview += f" — {AGREE[lang]}"
    if data.get('car'):
        preview += f"\n{data['car']}"
    if data.get('comment'):
        preview += f"\n{data['comment']}"
    kb = build_keyboard([(t(lang, 'driver.confirm'), 'confirm:yes')])
    await message.answer(preview, reply_markup=kb)


@router.callback_query(CreateTrip.confirm, F.data == 'confirm:yes')
async def confirm(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    data = await state.get_data()
    trip = Trip(
        id=uuid.uuid4(),
        driver_id=callback.from_user.id,
        from_city=data['from_city'],
        to_city=data['to_city'],
        departure_date=data['date'],
        time=data.get('time'),
        seats=data['seats'],
        price=data.get('price'),
        phone=data['phone'],
        car=data.get('car'),
        photos=data.get('photos', []),
        comment=data.get('comment'),
    )
    await storage.create_trip(trip)
    await callback.message.edit_text('✅')
    await callback.answer()
    await state.clear()
