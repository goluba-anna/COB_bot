import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ---------------- ЛОГИ ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- БОТ ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ---------------- СОСТОЯНИЯ ----------------
class Form(StatesGroup):
    consent = State()
    diagnostics = State()

# ---------------- START ----------------
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    username = message.from_user.first_name or "друг"
    
    text = f"""Привет, {username}! ❤️

Бывает, что жизнь будто ходит по кругу.
Это не случайность — это скрытые программы.

Я покажу твои топ-3 активные программы за 2–3 минуты.
Готов(а)?"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать диагностику", callback_data="start_diagnostics")]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(Form.consent)

# ---------------- CALLBACK ----------------
@dp.callback_query(lambda c: c.data == "start_diagnostics")
async def start_diagnostics(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично. Первый вопрос скоро появится ❤️")
    await state.set_state(Form.diagnostics)
    await callback.answer()

# ---------------- STARTUP ----------------
async def on_startup(bot: Bot):
    # УПРОЩЕНО: просто берем URL из переменной и устанавливаем вебхук
    webhook_url = os.getenv("WEBHOOK_URL")  # Прямая ссылка без изменений
    logger.info(f"Устанавливаю вебхук на: {webhook_url}")
    
    if webhook_url:
        await bot.set_webhook(url=webhook_url)
        logger.info("Вебхук успешно установлен")
    else:
        logger.error("WEBHOOK_URL не найден!")

# ---------------- SHUTDOWN ----------------
async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("Вебхук удалён")

# ---------------- MAIN ----------------
async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    
    # Регистрируем вебхук
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"Бот запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
