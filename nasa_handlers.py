import asyncio
import logging
import random
from datetime import date, datetime, timedelta
from io import BytesIO
from PIL import Image
from typing import Dict, Optional, Any

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, 
    CallbackQuery,
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    BufferedInputFile
)

from config import NASA_API_KEY
from data.rovers import ROVERS
from utils.cache import cache_response
from utils.http import nasa_client
from utils.monitoring import track_performance
import keyboards

logger = logging.getLogger(__name__)
router = Router()

MAX_IMAGE_SIZE = (1280, 1280)

async def optimize_image(image_data: bytes, max_size: tuple = MAX_IMAGE_SIZE) -> bytes:
    try:
        with BytesIO(image_data) as img_file:
            img = Image.open(img_file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            return output.getvalue()
    except Exception as e:
        logger.error(f"Error optimizing image: {e}")
        return image_data

@cache_response(cache_type='asteroids')
async def fetch_asteroids(today_date: str) -> Optional[Dict[str, Any]]:
    try:
        params = {
            "api_key": NASA_API_KEY,
            "start_date": today_date,
            "end_date": today_date
        }
        return await nasa_client.get("/neo/rest/v1/feed", params=params)
    except Exception as e:
        logger.error(f"Error fetching asteroids: {e}")
        return None

@cache_response(cache_type='mars_photos')
async def fetch_rover_latest_photos(rover: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"mars-photos/api/v1/rovers/{rover}/latest_photos"
        return await nasa_client.get(url, params={"api_key": NASA_API_KEY})
    except Exception as e:
        logger.error(f"Error fetching rover photos: {e}")
        return None

@cache_response(cache_type='earth_imagery')
async def fetch_earth_image(lat: float, lon: float, date_str: str) -> Optional[bytes]:
    try:
        params = {
            "api_key": NASA_API_KEY,
            "lat": lat,
            "lon": lon,
            "dim": 0.3,
            "date": date_str
        }
        return await nasa_client.get_bytes("/planetary/earth/imagery", params=params)
    except Exception as e:
        logger.warning(f"Failed to get earth image for {date_str}: {e}")
        return None

@router.message(CommandStart())
@router.message(F.text == "« Назад")
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я космический бот NASA. Я могу показать вам:\n"
        "☄️ Информацию о приближающихся астероидах\n"
        "🌞 Информацию о планетах Солнечной системы\n"
        "🌍 Спутниковые снимки Земли\n"
        "🔴 Фотографии с Марса\n"
        "✨ Каталог экзопланет\n"
        "❓ Космическую викторину\n\n"
        "Используйте клавиатуру ниже для навигации:",
        reply_markup=keyboards.main_keyboard
    )

@router.message(F.text == "☄️ Астероиды")
@track_performance()
async def get_asteroids(message: Message) -> None:
    try:
        today = date.today().isoformat()
        data = await fetch_asteroids(today)
        if not data:
            await message.answer("Ошибка при получении данных от NASA. Попробуйте позже.")
            return
            
        asteroids = data.get('near_earth_objects', {}).get(today, [])
        if not asteroids:
            await message.answer("На сегодня нет данных об астероидах. Попробуйте позже.")
            return
            
        asteroids.sort(
            key=lambda x: float(x['close_approach_data'][0]['miss_distance']['kilometers'])
        )
        
        for ast in asteroids[:5]:
            try:
                avg_size = (
                    ast['estimated_diameter']['meters']['estimated_diameter_min'] +
                    ast['estimated_diameter']['meters']['estimated_diameter_max']
                ) / 2
                text = (
                    f"☄️ <b>Астероид: {ast['name']}</b>\n\n"
                    f"📏 Размер: {ast['estimated_diameter']['meters']['estimated_diameter_min']:.1f}"
                    f"-{ast['estimated_diameter']['meters']['estimated_diameter_max']:.1f} м (средний: {avg_size:.1f} м)\n"
                    f"⚠️ Опасен: {'Да ☢️' if ast['is_potentially_hazardous_asteroid'] else 'Нет ✅'}\n"
                    f"🔺 Расстояние: {float(ast['close_approach_data'][0]['miss_distance']['kilometers']):,.0f} км\n"
                    f"🚀 Скорость: {float(ast['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']):,.0f} км/ч\n"
                    f"⏰ Время сближения: {ast['close_approach_data'][0]['close_approach_date_full']}"
                )
                await message.answer(text, parse_mode="HTML")
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error sending asteroid {ast.get('name')}: {e}")
    except Exception as e:
        logger.error(f"Error getting asteroids: {e}")
        await message.answer("Произошла ошибка при получении данных об астероидах.")

@router.message(F.text == "🔴 Марс")
@track_performance()
async def get_mars_photos(message: Message) -> None:
    try:
        buttons = []
        for rover_id, rover_info in ROVERS.items():
            if rover_id in ['curiosity', 'perseverance']:
                buttons.append([InlineKeyboardButton(
                    text=f"🤖 {rover_info['name']}",
                    callback_data=f"get_rover_photo:{rover_id}"
                )])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            "🔴 <b>Марсианские исследования</b>\n\n"
            "Выберите марсоход для просмотра последних фотографий:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending rover keyboard: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data.startswith("get_rover_photo"))
async def get_rover_photo(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
        _, rover = callback.data.split(":")
        
        data = await fetch_rover_latest_photos(rover)
        if not data or not data.get('latest_photos'):
            await callback.message.answer(
                f"Не удалось получить фотографии для марсохода {ROVERS[rover]['name']}. Попробуйте позже."
            )
            return

        photo = random.choice(data['latest_photos'])
        image_data = await nasa_client.get_bytes(photo['img_src'])
        optimized_image = await optimize_image(image_data)

        caption = (
            f"📸 Фото с марсохода {photo['rover']['name']}\n"
            f"📅 Дата съёмки: {photo['earth_date']}\n"
            f"🎥 Камера: {photo['camera']['full_name']}\n"
            f"📍 Сол: {photo.get('sol', 'N/A')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё фото", callback_data=f"get_rover_photo:{rover}")],
            [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
        ])

        await callback.message.answer_photo(
            photo=BufferedInputFile(optimized_image, "mars.jpg"),
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error handling rover photo: {e}")
        await callback.message.answer("Произошла ошибка при получении фотографий.")

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message) -> None:
    await message.answer(
        "🚀 Команды бота:\n\n"
        "/start - Начать работу с ботом\n"
        "☄️ Астероиды - Информация о околоземных астероидах\n"
        "🌞 Солнечная система - Информация о планетах\n"
        "🌍 Земля - Спутниковые снимки Земли\n"
        "🔴 Марс - Фотографии с марсоходов\n"
        "✨ Экзопланеты - Каталог экзопланет\n"
        "❓ Викторина - Космическая викторина с рангами\n\n"
        "📊 Викторина / Лидеры:\n"
        "/leaderboard - Таблица лидеров\n"
        "/profile - Мой профиль"
    )

@router.message(F.text == "🌍 Земля")
async def get_earth_image(message: Message) -> None:
    await message.answer(
        "Для получения спутникового снимка, отправьте геопозицию с помощью кнопки ниже "
        "или введите координаты вручную в формате:\n"
        "широта,долгота (например: 55.7558,37.6173)",
        reply_markup=keyboards.get_earth_keyboard()
    )

async def process_coordinates_logic(message: Message, lat: float, lon: float) -> None:
    try:
        loading_message = await message.answer("🔄 Загружаю спутниковый снимок...")
        
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            await loading_message.edit_text(
                "⚠️ Некорректные координаты! Широта должна быть от -90 до 90, долгота от -180 до 180."
            )
            return
        
        today = date.today()
        dates_to_try = [today - timedelta(days=x) for x in [0, 30, 60, 90, 180]]
        
        image_data = None
        used_date = None
        
        for try_date in dates_to_try:
            image_data = await fetch_earth_image(lat, lon, try_date.isoformat())
            if image_data:
                used_date = try_date
                break
        
        if not image_data:
            await loading_message.edit_text(
                "❌ Не удалось найти спутниковые снимки для этих координат. Попробуйте другие."
            )
            return
            
        optimized_image = await optimize_image(image_data)
        await loading_message.delete()
        
        caption = (
            f"🌍 Спутниковый снимок локации:\n"
            f"📍 Широта: {lat:.4f}°\n"
            f"📍 Долгота: {lon:.4f}°\n"
            f"📅 Дата снимка: {used_date.strftime('%d.%m.%Y')}"
        )
        
        await message.answer_photo(
            photo=BufferedInputFile(optimized_image, "earth.jpg"),
            caption=caption,
            reply_markup=keyboards.main_keyboard
        )
    except Exception as e:
        logger.error(f"Error getting Earth image: {e}")
        await message.answer("❌ Произошла ошибка при получении снимка.")

@router.message(F.location)
@track_performance()
async def process_location(message: Message) -> None:
    lat = message.location.latitude
    lon = message.location.longitude
    await process_coordinates_logic(message, lat, lon)

@router.message(F.text.regexp(r'^-?\d+\.?\d*,-?\d+\.?\d*$'))
@track_performance()
async def process_text_coordinates(message: Message) -> None:
    try:
        lat, lon = map(float, message.text.split(','))
        await process_coordinates_logic(message, lat, lon)
    except ValueError:
        await message.answer(
            "⚠️ Неверный формат координат. Пожалуйста, используйте формат: широта,долгота\n"
            "Например: 55.7558,37.6173"
        )

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Выберите интересующий вас раздел:",
        reply_markup=keyboards.main_keyboard
    )
    await callback.answer()
