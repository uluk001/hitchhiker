from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query()
async def show_number(callback: CallbackQuery):
    await callback.answer('номер раскрыт')
