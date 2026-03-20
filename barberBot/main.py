import asyncio
import logging
import os
import sys

# ==========================================
# 🚑 ЭКСТРЕННАЯ НАСТРОЙКА ПУТЕЙ (DOCKER FIX)
# ==========================================
# Добавляем папку /app/web в пути Python, чтобы он видел 'shop' и 'web.settings'
# В Docker мы точно знаем, что код лежит в /app
sys.path.append('/app/web')

# На всякий случай добавляем корень проекта
sys.path.append('/app')

# Теперь импортируем и запускаем Django
import django_setup
# ==========================================

from aiogram import Bot, Dispatcher


# Если ты перенес config.py в папку barberBot, то импорт сработает:
from config import BOT_TOKEN, TIMEZONE

# Импортируем роутеры (с защитой, если имена файлов отличаются)
try:
    from handlers.admin_private import admin_router
except ImportError:
    from handlers.admin_private import router as admin_router

try:
    from handlers.master_bot import user_router
except ImportError:
    from handlers.master_bot import router as user_router



async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(admin_router)
    dp.include_router(user_router)

    logging.info("🚀 Бот успешно запущен! Пути настроены.")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    from logging.handlers import RotatingFileHandler

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        force=True,
        handlers=[
            RotatingFileHandler("bot_logs.txt", maxBytes=1024 * 1024, backupCount=2, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")