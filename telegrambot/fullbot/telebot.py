import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from database import create_tables, new_quiz
from aiogram import F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import update_quiz_index, get_quiz_index, get_question, new_quiz, get_user_last_score, save_user_score
from quiz_data import quiz_data

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

API_TOKEN = '6472775643:AAFAPKKj-ldy73U7opf8G6sLt988omuaA6E'

bot = Bot(token=API_TOKEN)

dp = Dispatcher()

DB_NAME = 'quiz_bot.db'

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    current_question_index = await get_quiz_index(callback.from_user.id)
    
    correct_option = quiz_data[current_question_index]['correct_option']
    await callback.message.answer(f"Выбранный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    await callback.message.answer("Верно!")
    score = await get_user_last_score(callback.from_user.id)
    score += 1
    await save_user_score(callback.from_user.id, score)

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
        score = await get_user_last_score(callback.from_user.id) 
        await save_user_score(callback.from_user.id, score)    
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")              

@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    current_question_index = await get_quiz_index(callback.from_user.id)

    incorrect_option = quiz_data[current_question_index]['incorrect_option']
    await callback.message.answer(f"Выбранный ответ: {quiz_data[current_question_index]['options'][incorrect_option]}")

    correct_option = quiz_data[current_question_index]['correct_option']
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    score = await get_user_last_score(callback.from_user.id)
    await save_user_score(callback.from_user.id, score)

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        
# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик две кнопки
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

@dp.message(F.text=="Статистика")
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    score = await get_user_last_score(user_id) or 0
    await message.answer(f"Ваш результат: {score}")

async def main():

    await create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())