import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Конфигурация OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Конфигурация Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Конфигурация базы данных
DATABASE_NAME = 'user_conversations.db'

# Другие настройки
DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 't')