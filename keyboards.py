from typing import List
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

main_keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="☄️ Астероиды"), KeyboardButton(text="🌞 Солнечная система")],
        [KeyboardButton(text="🌍 Земля"), KeyboardButton(text="🔴 Марс")],
        [KeyboardButton(text="✨ Экзопланеты"), KeyboardButton(text="❓ Викторина")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию"
)

mars_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Curiosity", callback_data="mars_curiosity"),
        InlineKeyboardButton(text="Perseverance", callback_data="mars_perseverance")
    ],
    [InlineKeyboardButton(text="Opportunity", callback_data="mars_opportunity")],
    [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
])

quiz_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Легкий", callback_data="quiz_easy"),
        InlineKeyboardButton(text="Средний", callback_data="quiz_medium"),
        InlineKeyboardButton(text="Сложный", callback_data="quiz_hard")
    ],
    [
        InlineKeyboardButton(text="🏆 Таблица лидеров", callback_data="quiz_leaderboard"),
        InlineKeyboardButton(text="🎖️ Мой профиль", callback_data="quiz_profile")
    ],
    [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
])

exoplanets_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🌎 Kepler-452b", callback_data="exo_kepler_452b"),
        InlineKeyboardButton(text="🌍 Proxima b", callback_data="exo_proxima_b")
    ],
    [
        InlineKeyboardButton(text="🌎 TRAPPIST-1e", callback_data="exo_trappist_1e"),
        InlineKeyboardButton(text="🌍 K2-18b", callback_data="exo_k2_18b")
    ],
    [
        InlineKeyboardButton(text="🌎 Teegarden b", callback_data="exo_teegarden_b"),
        InlineKeyboardButton(text="🌍 LHS 1140b", callback_data="exo_lhs_1140b")
    ],
    [
        InlineKeyboardButton(text="🌎 GJ 257d", callback_data="exo_gj_257d"),
        InlineKeyboardButton(text="🌍 Ross 128b", callback_data="exo_ross_128b")
    ],
    [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
])

def get_planets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="☀️ Солнце", callback_data="planet_sun"),
            InlineKeyboardButton(text="☿️ Меркурий", callback_data="planet_mercury"),
            InlineKeyboardButton(text="♀️ Венера", callback_data="planet_venus")
        ],
        [
            InlineKeyboardButton(text="🌍 Земля", callback_data="planet_earth"),
            InlineKeyboardButton(text="♂️ Марс", callback_data="planet_mars")
        ],
        [
            InlineKeyboardButton(text="♃ Юпитер", callback_data="planet_jupiter"),
            InlineKeyboardButton(text="♄ Сатурн", callback_data="planet_saturn")
        ],
        [
            InlineKeyboardButton(text="⛢ Уран", callback_data="planet_uranus"),
            InlineKeyboardButton(text="♆ Нептун", callback_data="planet_neptune")
        ],
        [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
    ])

def get_quiz_answer_keyboard(options: List[str], correct_index: int) -> InlineKeyboardMarkup:
    keyboard = []
    for i, option in enumerate(options):
        callback_data = f"quiz_answer_{i}_{1 if i == correct_index else 0}"
        keyboard.append([InlineKeyboardButton(text=option, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mars_photos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Другое фото", callback_data="mars_next"),
            InlineKeyboardButton(text="🎥 Другая камера", callback_data="mars_camera")
        ],
        [InlineKeyboardButton(text="📅 Другой день", callback_data="mars_date")],
        [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]
    ])

def get_earth_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геопозицию", request_location=True)],
            [KeyboardButton(text="« Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправьте геопозицию или координаты"
    )