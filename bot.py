import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Настраиваем логи (чтобы видеть, что происходит в Railway)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота берётся из переменных окружения Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Порт из переменной PORT (Railway сам её задаёт)
PORT = int(os.getenv("PORT", 8080))

# Базовый путь webhook (должен совпадать с /webhook в setWebhook)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'cobbot-production-dd4e.up.railway.app')}{WEBHOOK_PATH}"

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Приветственное сообщение и кнопки
@router.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, я готов начать диагностику", callback_data="start_diagnostic")],
        [InlineKeyboardButton(text="О методе СОВ", callback_data="about_method")]
    ])
    await message.answer(
        "Привет! 👋\n\n"
        "Я помогу тебе пройти диагностику по методу СОВ и узнать свои активные программы.\n\n"
        "Выбери, что хочешь сделать:",
        reply_markup=keyboard
    )

# Пока просто заглушка на любое другое сообщение
@router.message()
async def echo_handler(message: Message):
    await message.answer("Привет! Я работаю. Напиши /start для начала 😊")

# Запуск webhook-сервера
async def on_startup(bot: Bot):
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён")

def main():
    app = web.Application()
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Запускаем сервер
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
