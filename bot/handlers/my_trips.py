from aiogram import Router, F
from aiogram.types import Message
from ..storage import MemoryStorage

router = Router()


@router.message(F.text == '/my_trips')
async def list_trips(message: Message):
    storage: MemoryStorage = message.bot['storage']
    trips = storage.list_driver_trips(message.from_user.id)
    if not trips:
        await message.answer('У вас нет активных поездок')
    else:
        await message.answer(f'У вас {len(trips)} поездок')
