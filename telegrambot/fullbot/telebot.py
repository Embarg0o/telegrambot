import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from database import create_tables, new_quiz
from aiogram import F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import update_quiz_index, get_quiz_index, get_question, new_quiz, update_quiz_results
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

    # await update_quiz_results(callback.from_user.id, score)

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
    
    # Получение текущего пользователя
    user_id = callback.from_user.id

    # Увеличение счета игрока на 1
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT score FROM quiz_results WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()

            if result is not None:
                # Если результат уже существует, увеличиваем счет
                score = result[0] + 1
                await db.execute('UPDATE quiz_results SET score = ? WHERE user_id = ?', (score, user_id))
            else:
                # Если результат не существует, создаем новую запись
                score = 1
                await db.execute('INSERT INTO quiz_results (user_id, score) VALUES (?, ?)', (user_id, score))

        await db.commit()


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

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
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT user_id, score FROM quiz_results ORDER BY score DESC
        ''') as cursor:
            results = await cursor.fetchall()

    # Выведи статистику игроков
    if len(results) == 0:
        await message.answer("Пока нет результатов прохождения квиза.")
    else:
        statistics = []
        for row in results:
            user = await bot.get_chat(row[0])
            statistics.append(f"@{user.username}: {row[1]}")
        await message.answer("Статистика игроков:\n\n" + "\n".join(statistics))

async def main():

    await create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())