import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
import time
import json

# Загрузка переменных окружения
from dotenv import load_dotenv

load_dotenv()

# Получение API ключей и ID ассистента
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Проверка наличия ключей
if not OPENAI_API_KEY or not TELEGRAM_TOKEN or not ASSISTANT_ID:
    raise ValueError("Отсутствуют необходимые переменные окружения. Проверьте файл .env")

# Инициализация клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Инициализация базы данных
conn = sqlite3.connect('user_conversations.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS conversations
             (user_id INTEGER, message TEXT, timestamp TEXT)''')
conn.commit()


def save_message_to_db(user_id, message, is_user=True):
    timestamp = datetime.now().isoformat()
    role = "user" if is_user else "assistant"
    c.execute("INSERT INTO conversations VALUES (?, ?, ?)", (user_id, f"{role}: {message}", timestamp))
    conn.commit()


def save_conversation_to_file(user_id, message, is_user=True):
    timestamp = datetime.now().isoformat()
    role = "User" if is_user else "Assistant"
    filename = f"conversation_{user_id}.txt"

    # Чтение существующего содержимого файла
    existing_content = ""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            existing_content = file.read()

    # Добавление нового сообщения
    with open(filename, "w", encoding="utf-8") as file:
        if existing_content:
            file.write(existing_content + "\n")
        file.write(f"{timestamp} - {role}: {message}\n")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш ассистент по здоровому питанию и образу жизни. Чем могу помочь?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    save_message_to_db(user_id, user_message)
    save_conversation_to_file(user_id, user_message)

    try:
        # Создание нового потока для каждого сообщения
        thread = client.beta.threads.create()

        # Добавление сообщения пользователя в поток
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # Запуск ассистента
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Ожидание завершения выполнения
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(1)

        # Получение ответа ассистента
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_message = messages.data[0].content[0].text.value

    except Exception as e:
        print(f"Ошибка при запросе к OpenAI: {e}")
        assistant_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

    await update.message.reply_text(assistant_message)

    save_message_to_db(user_id, assistant_message, is_user=False)
    save_conversation_to_file(user_id, assistant_message, is_user=False)


async def get_conversation_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    filename = f"conversation_{user_id}.txt"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            conversation = file.read()
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