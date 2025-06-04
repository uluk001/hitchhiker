from __future__ import annotations

import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery

from ..config import Config
from ..i18n import t
from ..storage import Storage
from ..utils import build_keyboard, schedule_followup
from aiogram import Bot

router = Router()


@router.callback_query(F.data.startswith("phone:"))
async def show_phone(callback: CallbackQuery, storage: Storage, config: Config, bot: Bot) -> None:
    trip_id = callback.data.split(":", 1)[1]
    trip = await storage.get_trip(uuid.UUID(trip_id))
    if not trip:
        await callback.answer("❌")
        return
    lang = await storage.get_language(callback.from_user.id, config.default_language)
    await callback.message.answer(trip.phone)
    await storage.record_contact(trip.id, callback.from_user.id)
    follow_kb = build_keyboard([
        (t(lang, 'followup.full'), f'full:{trip.id}'),
        (t(lang, 'followup.not_yet'), f'wait:{trip.id}'),
        (t(lang, 'followup.delete'), f'del:{trip.id}')
    ])
    await schedule_followup(bot, trip.driver_id, t(lang, 'followup.message'), config.followup_delay, follow_kb)
    await callback.answer()


@router.callback_query(F.data.startswith(('full:', 'wait:', 'del:')))
async def handle_follow(callback: CallbackQuery, storage: Storage) -> None:
    action, trip_id = callback.data.split(":", 1)
    if action == 'del' or action == 'full':
        await storage.delete_trip(uuid.UUID(trip_id))
    await callback.answer("✅")
