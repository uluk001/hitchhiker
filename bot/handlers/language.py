from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='🇷🇺'), KeyboardButton(text='🇰🇬')]], resize_keyboard=True
    )
    await message.answer('Выберите язык / Тилди тандаңыз', reply_markup=kb)
