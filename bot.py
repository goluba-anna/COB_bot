import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

# Импорты для aiohttp webhook (это критично!)
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Бот и диспетчер
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния
class Form(StatesGroup):
    consent = State()
    diagnostics = State()

# /start
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    username = message.from_user.first_name or "друг"
    text = f"""Привет, {username}! ❤️

Бывает, что жизнь будто ходит по одному и тому же кругу:  
одни и те же ссоры в отношениях, деньги утекают сквозь пальцы, настроение качается как на качелях…  
Знакомо?  

Это не случайности. Это твои скрытые программы, которые тихо управляют решениями.

Я — бот метода <b>СОВ (Системы Осознанного Выбора)</b>.  
За 2–3 минуты честных ответов покажу твои топ-3 самые активные программы и как именно они влияют на твою жизнь прямо сейчас.

Хочешь посмотреть правду о себе и понять, где можно всё изменить? 👀"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Начать диагностику", callback_data="start_diagnostics"),
            InlineKeyboardButton(text="О методе СОВ", callback_data="about_method"),
            InlineKeyboardButton(text="Условия и документы", callback_data="show_legal")
        ]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(Form.consent)

# Начать диагностику
@dp.callback_query(lambda c: c.data == "start_diagnostics")
async def start_diagnostics_callback(callback: types.CallbackQuery, state: FSMContext):
    text = """Прежде чем мы начнём диагностику, нужно подтвердить согласие с условиями:

• Ты соглашаешься с публичной офертой  
• Даёшь согласие на обработку персональных данных  
• Разрешаешь присылать тебе полезные материалы и напоминания (можно отписаться в любой момент)

Это стандартные правила, чтобы всё было честно и безопасно.

Если хочешь почитать документы подробнее — нажми кнопку ниже.

Готов(а) продолжить? 😊"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласен(а) и готов(а) начать", callback_data="confirm_consent")],
        [InlineKeyboardButton(text="Условия и документы", callback_data="show_legal")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# О методе СОВ
@dp.callback_query(lambda c: c.data == "about_method")
async def about_method_callback(callback: types.CallbackQuery):
    text = """📚 О методе СОВ — Системы Осознанного Выбора

СОВ — это простой и системный подход, который помогает увидеть, какие скрытые программы управляют вашими решениями и повторяющимися ситуациями в жизни.

Он соединяет психологию и силу осознанного выбора, чтобы вы могли перестать жить "на автопилоте" и начать менять то, что давно мешает.

Основные принципы:
• Системность — ваша психика как целое
• Осознанность — замечать автоматические реакции
• Выбор — принимать решения, которые действительно ваши

Программы — это шаблоны поведения из детства, которые влияют на отношения, деньги, карьеру и самооценку.

Диагностика покажет ваши топ-3 программы за 2–3 минуты и даст понимание, как они влияют на жизнь сейчас.

Готовы начать? Нажмите «Начать диагностику» ❤️"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать диагностику", callback_data="start_diagnostics")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Подтверждение согласия
@dp.callback_query(lambda c: c.data == "confirm_consent")
async def confirm_consent(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Начинаем диагностику ❤️\n\nСейчас первый вопрос...")
    await callback.message.answer("Вопрос 1 из 20: ... (пока заглушка)")
    await state.set_state(Form.diagnostics)
    await callback.answer()

# Условия и документы
@dp.callback_query(lambda c: c.data == "show_legal")
async def show_legal(callback: types.CallbackQuery):
    text = """📄 Условия и документы

• <a href="https://drive.google.com/file/d/1hNsbGW4igNVqJXjl3tApcbSXrNQiX27K/view?usp=sharing">Публичная оферта</a>  
• <a href="https://drive.google.com/file/d/1lP5d-MCBvNpxNBV1hZSCRHByWgFz5LEP/view?usp=sharing">Согласие на обработку персональных данных</a>  
• <a href="https://drive.google.com/file/d/1Z3250DPzMun4fuijStmcgIBN8H36-vKy/view?usp=sharing">Согласие на получение уведомлений</a>

После ознакомления просто вернись и нажми «Начать диагностику» ❤️"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в начало", callback_data="back_to_start")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

# Возврат в начало
@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await start_handler(callback.message, state)
    await callback.answer()

# Запуск
async def on_startup(bot: Bot):
    try:
        raw_url = os.getenv("WEBHOOK_URL")
        logger.info(f"RAW WEBHOOK_URL: {repr(raw_url)}")

        webhook_url = f"{raw_url}/webhook"
        logger.info(f"FULL WEBHOOK_URL: {repr(webhook_url)}")

        secret = os.getenv("WEBHOOK_SECRET", "secret")

        if not raw_url or not secret:
            logger.error("Отсутствует WEBHOOK_URL или WEBHOOK_SECRET!")
            return

        await bot.set_webhook(url=webhook_url, secret_token=secret)
        logger.info(f"Webhook установлен: {webhook_url}")

    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

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
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    logger.info("Сервер запущен и ожидает обновлений")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
