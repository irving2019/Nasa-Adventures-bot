import logging
import random
from datetime import date

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

import keyboards
from utils.db import get_user, save_user, get_leaderboard

logger = logging.getLogger(__name__)
router = Router()

class QuizState(StatesGroup):
    waiting_for_answer = State()

QUIZ_QUESTIONS = {
    "easy": [
        {
            "question": "Какая планета находится ближе всего к Солнцу?",
            "options": ["Венера", "Меркурий", "Марс", "Земля"],
            "correct": 1
        },
        {
            "question": "Как называется галактика, в которой находится наша Солнечная система?",
            "options": ["Андромеда", "Млечный Путь", "Треугольник", "Сомбреро"],
            "correct": 1
        },
        {
            "question": "Какая планета известна своими кольцами?",
            "options": ["Юпитер", "Уран", "Сатурн", "Нептун"],
            "correct": 2
        }
    ],
    "medium": [
        {
            "question": "Какой спутник является крупнейшим в Солнечной системе?",
            "options": ["Титан", "Европа", "Ганимед", "Фобос"],
            "correct": 2
        },
        {
            "question": "Какое созвездие также известно как 'Большой Ковш'?",
            "options": ["Кассиопея", "Большая Медведица", "Орион", "Лебедь"],
            "correct": 1
        },
        {
            "question": "Сколько времени требуется свету, чтобы достичь Земли от Солнца?",
            "options": ["4 минуты", "8 минут", "16 минут", "32 минуты"],
            "correct": 1
        }
    ],
    "hard": [
        {
            "question": "Какой объект считается первой обнаруженной экзопланетой?",
            "options": ["51 Пегаса b", "Kepler-186f", "HD 209458 b", "TRAPPIST-1e"],
            "correct": 0
        },
        {
            "question": "Какой тип звезды станет наше Солнце в конце своей жизни?",
            "options": ["Красный гигант", "Белый карлик", "Нейтронная звезда", "Черная дыра"],
            "correct": 1
        },
        {
            "question": "Какое явление описывает гравитационное искривление света?",
            "options": ["Красное смещение", "Линзирование", "Аберрация", "Параллакс"],
            "correct": 1
        }
    ]
}

def get_rank(score: int) -> str:
    if score >= 150:
        return "🌌 Межгалактический исследователь"
    elif score >= 100:
        return "🚀 Космический путешественник"
    elif score >= 60:
        return "👨‍🚀 Астронавт"
    elif score >= 20:
        return "🛰️ Кадет"
    else:
        return "🔭 Наблюдатель"

@router.message(F.text == "❓ Викторина")
async def start_quiz(message: Message):
    await message.answer(
        "Добро пожаловать в космическую викторину! 🚀\n"
        "Выберите уровень сложности или просмотрите свои рекорды:",
        reply_markup=keyboards.quiz_keyboard
    )

@router.callback_query(F.data.startswith("quiz_"))
async def handle_quiz_actions(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "leaderboard":
        await show_leaderboard_action(callback)
        return
    elif action == "profile":
        await show_profile_action(callback)
        return
        
    difficulty = action
    question = random.choice(QUIZ_QUESTIONS[difficulty])
    
    await state.update_data(
        current_question=question,
        difficulty=difficulty
    )
    
    options_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"answer_{i}")]
            for i, option in enumerate(question["options"])
        ] + [[InlineKeyboardButton(text="« Главное меню", callback_data="main_menu")]]
    )
    
    await callback.message.answer(
        f"Вопрос ({difficulty}):\n\n{question['question']}",
        reply_markup=options_keyboard
    )
    
    await state.set_state(QuizState.waiting_for_answer)
    await callback.answer()

@router.callback_query(F.data.startswith("answer_"), QuizState.waiting_for_answer)
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    user_answer = int(callback.data.split("_")[1])
    data = await state.get_data()
    question = data["current_question"]
    difficulty = data["difficulty"]
    
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    # Загружаем текущую статистику
    user_stats = get_user(user_id)
    if not user_stats:
        user_stats = {'score': 0, 'correct_answers': 0, 'total_answers': 0, 'username': username}
        
    correct = (user_answer == question["correct"])
    
    points = 10 if correct else 0
    new_score = user_stats['score'] + points
    new_correct = user_stats['correct_answers'] + (1 if correct else 0)
    new_total = user_stats['total_answers'] + 1
    
    save_user(user_id, username, new_score, new_correct, new_total, date.today().isoformat())
    
    rank = get_rank(new_score)
    
    if correct:
        await callback.message.answer(
            f"✅ Правильно! Вы получили +10 очков.\n"
            f"Ваш ранг: {rank} ({new_score} очков)\n\n"
            f"Хотите продолжить?",
            reply_markup=keyboards.quiz_keyboard
        )
    else:
        correct_answer = question["options"][question["correct"]]
        await callback.message.answer(
            f"❌ Неправильно. Правильный ответ: <tg-spoiler>{correct_answer}</tg-spoiler>\n"
            f"Ваш ранг: {rank} ({new_score} очков)\n\n"
            f"Хотите попробовать еще раз?",
            reply_markup=keyboards.quiz_keyboard
        )
    
    await state.clear()
    await callback.answer()

async def show_leaderboard_action(callback: CallbackQuery):
    leaders = get_leaderboard(10)
    if not leaders:
        await callback.message.answer("Таблица лидеров пока пуста. Будьте первым!")
        await callback.answer()
        return
        
    text = "🏆 <b>Таблица лидеров космической викторины</b> 🏆\n\n"
    for i, (username, score, correct) in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🛰️"
        text += f"{medal} {i}. <b>{username}</b> — {score} очков ({correct} верных ответов)\n"
        
    await callback.message.answer(text, reply_markup=keyboards.quiz_keyboard)
    await callback.answer()

async def show_profile_action(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    stats = get_user(user_id)
    
    if not stats:
        stats = {'score': 0, 'correct_answers': 0, 'total_answers': 0}
        
    accuracy = (stats['correct_answers'] / stats['total_answers'] * 100) if stats['total_answers'] > 0 else 0
    rank = get_rank(stats['score'])
    
    text = (
        f"🎖️ <b>Космический профиль: {username}</b>\n\n"
        f"🔹 Ранг: {rank}\n"
        f"🔹 Очки: {stats['score']}\n"
        f"🔹 Верных ответов: {stats['correct_answers']} из {stats['total_answers']}\n"
        f"🔹 Точность: {accuracy:.1f}%\n"
    )
    await callback.message.answer(text, reply_markup=keyboards.quiz_keyboard)
    await callback.answer()

@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    leaders = get_leaderboard(10)
    if not leaders:
        await message.answer("Таблица лидеров пока пуста. Будьте первым!")
        return
    text = "🏆 <b>Таблица лидеров космической викторины</b> 🏆\n\n"
    for i, (username, score, correct) in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🛰️"
        text += f"{medal} {i}. <b>{username}</b> — {score} очков ({correct} верных ответов)\n"
    await message.answer(text)

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    stats = get_user(user_id)
    if not stats:
        stats = {'score': 0, 'correct_answers': 0, 'total_answers': 0}
    accuracy = (stats['correct_answers'] / stats['total_answers'] * 100) if stats['total_answers'] > 0 else 0
    rank = get_rank(stats['score'])
    text = (
        f"🎖️ <b>Космический профиль: {username}</b>\n\n"
        f"🔹 Ранг: {rank}\n"
        f"🔹 Очки: {stats['score']}\n"
        f"🔹 Верных ответов: {stats['correct_answers']} из {stats['total_answers']}\n"
        f"🔹 Точность: {accuracy:.1f}%\n"
    )
    await message.answer(text)
