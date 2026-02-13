import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ---------------- ЛОГИ ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- БОТ ----------------
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ---------------- СОСТОЯНИЯ ----------------
class Form(StatesGroup):
    consent = State()
    diagnostics = State()

# ---------------- START ----------------
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
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
    try:
        raw_url = os.getenv("WEBHOOK_URL")
        logger.info(f"RAW WEBHOOK_URL: {repr(raw_url)}")

        if not raw_url:
            logger.error("WEBHOOK_URL не задан!")
            return

        webhook_url = f"{raw_url}/webhook"
        logger.info(f"FULL WEBHOOK_URL: {repr(webhook_url)}")

        secret = os.getenv("WEBHOOK_SECRET", "secret")

        await bot.set_webhook(
            url=webhook_url,
            secret_token=secret
        )

        logger.info("Webhook успешно установлен")

    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

# ---------------- SHUTDOWN ----------------
async def on_shutdown(bot: Bot):
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удалён")
    except Exception as e:
        logger.error(f"Ошибка удаления webhook: {e}")

# ---------------- MAIN ----------------
async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.getenv("WEBHOOK_SECRET", "secret")
    )

    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    logger.info(f"Запуск на порту: {port}")

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("Сервер запущен и ожидает обновлений")
    await asyncio.Event().wait()

# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
