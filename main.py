import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Получение API ключей
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Проверка наличия ключей
if not OPENAI_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Отсутствуют необходимые переменные окружения. Проверьте файл .env")

# Инициализация клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Инициализация базы данных
conn = sqlite3.connect('user_conversations.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS conversations
             (user_id INTEGER, message TEXT, timestamp TEXT)''')
conn.commit()


def save_message(user_id, message, is_user=True):
    timestamp = datetime.now().isoformat()
    role = "user" if is_user else "assistant"
    c.execute("INSERT INTO conversations VALUES (?, ?, ?)", (user_id, f"{role}: {message}", timestamp))
    conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш ассистент по здоровому питанию и образу жизни. Чем могу помочь?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    save_message(user_id, user_message)

    # Создание запроса к GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Вы ассистент по здоровому питанию и образу жизни. Используйте информацию из предоставленной базы знаний о кето-диете, интервальном голодании и здоровом образе жизни."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500  # Ограничение длины ответа
        )

        assistant_message = response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при запросе к OpenAI: {e}")
        assistant_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

    await update.message.reply_text(assistant_message)

    save_message(user_id, assistant_message, is_user=False)


async def get_conversation_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    c.execute("SELECT message FROM conversations WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    history = c.fetchall()

    if history:
        conversation = "\n".join([msg[0] for msg in history])
        await update.message.reply_text(f"Ваша история переписки:\n\n{conversation}")
    else:
        await update.message.reply_text("У вас пока нет истории переписки.")


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", get_conversation_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()