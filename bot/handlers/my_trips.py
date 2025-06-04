from __future__ import annotations

import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..storage import Storage
from ..utils import build_keyboard

router = Router()


@router.message(F.text.startswith("📋"))
async def list_trips(message: Message, storage: Storage) -> None:
    trips = await storage.list_driver_trips(message.from_user.id)
    if not trips:
        await message.answer("😔")
        return
    for trip in trips:
        text = f"{trip.from_city} ➡️ {trip.to_city} {trip.departure_date}"
        kb = build_keyboard([("🗑", f"del:{trip.id}")])
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_trip(callback: CallbackQuery, storage: Storage) -> None:
    trip_id = callback.data.split(":", 1)[1]
    await storage.delete_trip(uuid.UUID(trip_id))
    await callback.answer("✅", show_alert=False)
    await callback.message.delete()
