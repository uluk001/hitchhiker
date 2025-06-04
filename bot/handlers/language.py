from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from ..config import Config
from ..i18n import t
from ..storage import Storage

router = Router()

LANG_BUTTONS = {
    '🇷🇺 Русский': 'ru',
    '🇰🇬 Кыргызча': 'kg',
}


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, 'menu.create_trip')), KeyboardButton(text=t(lang, 'menu.search_trip'))],
            [KeyboardButton(text=t(lang, 'menu.my_trips'))],
        ],
        resize_keyboard=True,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, storage: Storage, config: Config) -> None:
    lang = await storage.get_language(message.from_user.id, None)
    if not lang:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=b) for b in LANG_BUTTONS]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(t(config.default_language, 'start.choose_language'), reply_markup=kb)
    else:
        await message.answer(t(lang, 'start.choose_language'), reply_markup=main_menu(lang))


@router.message(F.text.in_(LANG_BUTTONS.keys()))
async def set_lang(message: Message, storage: Storage) -> None:
    lang = LANG_BUTTONS[message.text]
    await storage.set_language(message.from_user.id, lang)
    await message.answer(t(lang, 'start.choose_language'), reply_markup=main_menu(lang))
