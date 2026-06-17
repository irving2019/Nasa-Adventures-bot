import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from utils.cache import clear_all_caches
from utils.monitoring import monitor

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("stats"))
async def show_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ разрешен только администраторам.")
        return
        
    try:
        stats = monitor.get_summary()
        text = "📊 Статистика бота\n\n"
        text += f"⏱ Время работы: {stats['uptime']}\n"
        text += f"📡 Всего API запросов: {stats['total_api_calls']}\n\n"
        
        text += "🔄 Статистика API:\n"
        for endpoint, data in stats['api_stats'].items():
            text += f"- {endpoint}:\n"
            text += f"  • Среднее время: {data['avg_time']}\n"
            text += f"  • Макс. время: {data['max_time']}\n"
            text += f"  • Мин. время: {data['min_time']}\n"
            text += f"  • Запросов: {data['calls']}\n"
        
        text += "\n📦 Статистика кэша:\n"
        for cache_type, data in stats['cache_stats'].items():
            text += f"- {cache_type}:\n"
            text += f"  • Hit ratio: {data['hit_ratio']}\n"
            text += f"  • Hits: {data['hits']}\n"
            text += f"  • Misses: {data['misses']}\n"
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer("Ошибка при получении статистики.")

@router.message(Command("cache_clear"))
async def clear_cache(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ разрешен только администраторам.")
        return
        
    try:
        await clear_all_caches()
        await message.answer("✅ Все кэши очищены.")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        await message.answer("Ошибка при очистке кэша.")
