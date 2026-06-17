import admin_handlers
import asyncio
import logging
import nasa_handlers
import planet_handlers
import quiz_handlers
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT, LOG_FILE
from utils.db import init_db

logger = logging.getLogger(__name__)

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiogram').setLevel(logging.WARNING)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(nasa_handlers.router)
dp.include_router(planet_handlers.router)
dp.include_router(quiz_handlers.router)
dp.include_router(admin_handlers.router)

async def main() -> None:
    logger.info("Initializing database...")
    init_db()
    
    logger.info("Starting bot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot %s started successfully", (await bot.get_me()).username)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Critical error: %s", e, exc_info=True)
        raise
    finally:
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        setup_logging()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        raise