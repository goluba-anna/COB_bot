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

from aiohttp import web   # ← добавь эту строку

load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class Form(StatesGroup):
    consent = State()          # ожидание согласия на условия
    diagnostics = State()      # прохождение диагностики (вопросы)

# Приветственное сообщение с тремя кнопками
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

# Обработка кнопки "Начать диагностику"
@dp.callback_query(lambda c: c.data == "start_diagnostics")
async def start_diagnostics_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        """Прежде чем мы начнём диагностику, нужно подтвердить согласие с условиями:

• Ты соглашаешься с публичной офертой  
• Даёшь согласие на обработку персональных данных  
• Разрешаешь присылать тебе полезные материалы и уведомления (можно отписаться в любой момент)

Это стандартные правила, чтобы всё было честно и безопасно.

Если хочешь почитать документы подробнее — нажми кнопку ниже.

Готов(а) продолжить? 😊""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Согласен(а) и готов(а) начать", callback_data="confirm_consent")],
            [InlineKeyboardButton(text="Условия и документы", callback_data="show_legal")]
        ])
    )
    await callback.answer()

# Обработка кнопки "О методе СОВ"
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

# Подтверждение согласия → начало диагностики
@dp.callback_query(lambda c: c.data == "confirm_consent")
async def confirm_consent(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Начинаем диагностику ❤️\n\nСейчас первый вопрос...")
    # Здесь будет переход к первому вопросу опроса
    # Пока просто заглушка
    await callback.message.answer("Вопрос 1 из 20: ... (тут будет твой вопрос)")
    await state.set_state(Form.diagnostics)
    await callback.answer()

# Показ документов
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

# Возврат в начало (если нужно)
@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await start_handler(callback.message, state)
    await callback.answer()

# Запуск бота (webhook)
async def on_startup(bot: Bot):
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=os.getenv("WEBHOOK_SECRET", "secret")
    )
    logger.info(f"Webhook set to {webhook_url}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.getenv("WEBHOOK_SECRET", "secret")
    ).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    logger.info("Server started")
    await asyncio.Event().wait()  # держим сервер живым

if __name__ == "__main__":
    asyncio.run(main())
