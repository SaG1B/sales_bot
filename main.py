import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import common, catalog, checkout

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем все роутеры
    dp.include_router(common.router)
    dp.include_router(catalog.router)
    dp.include_router(checkout.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())