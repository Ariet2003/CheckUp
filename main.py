# main.py
from aiogram import Dispatcher
from app.database.models import async_main
from bot_instance import bot, dp  # Импортируем bot и dp
from app.users.admin.adminHandlers import router
# from app.database.models import async_main
import asyncio

async def main():
    await async_main()  # Если бд sqlite
    dp.include_router(router)  # Убедитесь, что router подключён
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
