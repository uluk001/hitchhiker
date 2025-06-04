from __future__ import annotations

from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..config import Config
from ..i18n import t
from ..storage import Storage
from ..utils import build_keyboard

router = Router()


class SearchRide(StatesGroup):
    from_city = State()
    to_city = State()
    date = State()
    time_pref = State()


def city_kb(cfg: Config) -> list[tuple[str, str]]:
    return [(c, f"scity:{c}") for c in cfg.cities]


def time_kb(lang: str) -> list[tuple[str, str]]:
    return [
        ("🌅", "morning"),
        ("🌇", "afternoon"),
        ("🌆", "evening"),
        ("🌃", "night"),
    ]


@router.message(F.text.startswith("🔎"))
async def start_search(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    await state.set_state(SearchRide.from_city)
    await message.answer(t(lang, "passenger.from_city"), reply_markup=build_keyboard(city_kb(config)))


@router.callback_query(SearchRide.from_city, F.data.startswith("scity:"))
async def set_from(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await state.update_data(from_city=callback.data.split(":", 1)[1])
    await state.set_state(SearchRide.to_city)
    await callback.message.edit_text(t(lang, "passenger.to_city"), reply_markup=build_keyboard(city_kb(config)))
    await callback.answer()


@router.callback_query(SearchRide.to_city, F.data.startswith("scity:"))
async def set_to(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await state.update_data(to_city=callback.data.split(":", 1)[1])
    await state.set_state(SearchRide.date)
    buttons = [
        ("Сегодня", "d:0"),
        ("Завтра", "d:1"),
        ("Введите дату", "d:manual"),
    ]
    await callback.message.edit_text(t(lang, "passenger.date"), reply_markup=build_keyboard(buttons))
    await callback.answer()


@router.callback_query(SearchRide.date, F.data.startswith("d:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    data = callback.data.split(":", 1)[1]
    if data == "manual":
        await callback.message.edit_text(t(lang, "passenger.date") + " YYYY-MM-DD")
        await state.set_state(SearchRide.date)
        await state.update_data(manual_date=True)
    else:
        days = int(data)
        await state.update_data(date=date.today() + timedelta(days=days), manual_date=False)
        await state.set_state(SearchRide.time_pref)
        await callback.message.edit_text(t(lang, "passenger.time"), reply_markup=build_keyboard(time_kb(lang)))
    await callback.answer()


@router.message(SearchRide.date)
async def manual_date(message: Message, state: FSMContext, config: Config, storage: Storage) -> None:
    lang = await storage.get_language(message.from_user.id, config.default_language)
    try:
        chosen = date.fromisoformat(message.text)
    except ValueError:
        await message.answer(t(lang, "passenger.date") + " YYYY-MM-DD")
        return
    await state.update_data(date=chosen)
    await state.set_state(SearchRide.time_pref)
    await message.answer(t(lang, "passenger.time"), reply_markup=build_keyboard(time_kb(lang)))


@router.callback_query(SearchRide.time_pref)
async def show_rides(callback: CallbackQuery, state: FSMContext, config: Config, storage: Storage) -> None:
    data = await state.get_data()
    trips = await storage.search_trips(data['from_city'], data['to_city'], data['date'])
    if not trips:
        await callback.message.edit_text("😔")
        await callback.answer()
        await state.clear()
        return
    for trip in trips:
        text = f"{trip.from_city} ➡️ {trip.to_city}\n{trip.departure_date}"
        if trip.time:
            text += f" {trip.time.strftime('%H:%M')}"
        text += f"\n{trip.seats} seats"
        if trip.price:
            text += f" — {trip.price}"
        kb = build_keyboard([("📞", f"phone:{trip.id}")])
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()
    await state.clear()
