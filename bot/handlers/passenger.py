from aiogram import Router, F
from aiogram.types import Message
from datetime import date
from ..storage import Storage

router = Router()


@router.message(F.text == 'search')
async def cmd_search(message: Message):
    await message.answer('Из какого города?')


@router.message()
async def handle_city(message: Message, storage: Storage):
    # simplified search handler
    trips = await storage.search_trips(message.text, message.text, date.today())
    if not trips:
        await message.answer('Не найдено')
        return
    await message.answer(f'Найдено {len(trips)} поездок')
