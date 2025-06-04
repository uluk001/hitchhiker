import re
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Iterable


PHONE_REGEX = re.compile(r'^\+?\d{9,15}$')
TIME_REGEX = re.compile(r'^[0-2]\d:[0-5]\d$')


def validate_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone))


def validate_time(t: str) -> bool:
    return bool(TIME_REGEX.match(t))


def build_keyboard(buttons: Iterable[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data)] for text, data in buttons]
    )

import asyncio

async def schedule_followup(bot, chat_id: int, text: str, delay: int, keyboard: InlineKeyboardMarkup | None = None):
    await asyncio.sleep(delay)
    await bot.send_message(chat_id, text, reply_markup=keyboard)
