import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage as FSMStorage
from aiogram.types import Message
from .config import Config
from .storage import MemoryStorage
from .handlers import language, driver, passenger, followup, my_trips


async def main() -> None:
    config = Config.load('config.json')
    bot = Bot(token=config.token, parse_mode='HTML')
    dp = Dispatcher(storage=FSMStorage())

    storage = MemoryStorage()
    dp['config'] = config
    dp['storage'] = storage

    dp.include_router(language.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)
    dp.include_router(followup.router)
    dp.include_router(my_trips.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
