import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import (
    client,
    booking,
    admin,
    products,
    certificates
)
from handlers import subscription
from utils.scheduler import setup_scheduler
from middlewares import SubscriptionMiddleware


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем базу данных
    await db.init_db()

    # Подключаем middleware подписки
    dp.message.middleware(SubscriptionMiddleware())

    # Подключаем все роутеры
    dp.include_router(subscription.router)
    dp.include_router(client.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    dp.include_router(products.router)
    dp.include_router(certificates.router)

    # Запускаем планировщик напоминаний
    setup_scheduler(bot)

    print("✅ Бот запущен и работает!")
    print("Для остановки нажмите Ctrl+C")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())